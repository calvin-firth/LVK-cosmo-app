# Functions for performing the actual analysis and adding it to redis

import icarogw
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import h5py
import numpy as np
from astropy.cosmology import FlatLambdaCDM
from astropy import constants
import healpy as hp
from ligo.skymap.postprocess.crossmatch import crossmatch
import pandas as pd
import io
from base64 import b64decode
from io import BytesIO
from astropy.table import Table
np.random.seed(0)

def save_fig_redis(r, redis_key, field_name, fig=None):
    buf = io.BytesIO()
    if fig is None:
        fig = plt.gcf()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    r.hset(redis_key, field_name, buf.read())
    return

def analyze_event(name,skmap_file, cat, empty_cat,r,num_skmap=40000,Npar=25000,NeffPE=10):
    try:
        print("in func",flush=True)
        posterior_dict = {}
        print("before skmap",flush=True)
        skymap_bytes = b64decode(skmap_file)
        print("Past skymap bites")

        skmap = icarogw.conversions.ligo_skymap(BytesIO(skymap_bytes))
        print("after skmap",flush=True)
        dl, ra, dec = skmap.sample_3d_space(num_skmap)
        ind_arr = (dl != 0) & (~np.isinf(dl))
        dl = dl[ind_arr]
        ra = ra[ind_arr]
        dec = dec[ind_arr]
        areas = crossmatch(skmap.table, contours=(0.5, 0.9)).contour_areas

        r.hset(name,"50% area",areas[0])
        r.hset(name, "90% area", areas[1])
        r.hset(name, "dl", dl.mean())

        # We extract all the data we need for the event
        ppd = {'luminosity_distance': dl,  # Luminosity distance in Mpc
               'right_ascension': ra,  # right ascension in radians
               'declination': dec}  # Declination in radians

        # We initialize the posterior samples as usual
        try:
            posterior_dict['event'] = icarogw.posterior_samples.posterior_samples(ppd, prior=np.power(dl, 2.))
        except:
            r.hset(name, "status", "Analysis failed")
            return

        # This method below will pixelise the posterior samples in the sky and will add them under `sky_indices` in the posterior_data attribute
        posterior_dict['event'].pixelize_with_catalog(cat)
        pos_cat = icarogw.posterior_samples.posterior_samples_catalog(posterior_dict)

        # Just a plot of the skymap
        counts_map, domega = icarogw.conversions.radec2skymap(
            posterior_dict['event'].posterior_data['right_ascension'], posterior_dict['event'].posterior_data['declination'],
            nside=cat.moc_mthr_map.nside)

        fig = plt.figure()
        hp.mollview(counts_map, title=name,fig=fig)
        save_fig_redis(r,name,"skymap",fig=fig)

        # Again we need to tell icarogw what reference cosmology was used to build the catalog
        cosmo_ref = icarogw.cosmology.astropycosmology(zmax=25.)
        cosmo_ref.build_cosmology(FlatLambdaCDM(H0=67.7, Om0=0.308))

        zarr = np.linspace(((dl.mean() - dl.std()) * 20 / 300000), ((dl.mean() + dl.std()) * 140 / 300000), 200) # Show the relevant z-range (linear approximation)
        cat.sch_fun.build_MF(cosmo_ref)
        # The function below just check how the completeness and differential number density of galaxies look like
        gcp, bgp, inco, fig2, ax2 = cat.check_differential_effective_galaxies(zarr,
                                                                            posterior_dict['event'].posterior_data[
                                                                                'sky_indices'][:100:],
                                                                            cosmo_ref)
        ax2[0].set_title(name)
        ax2[0].set_ylabel(r'$\frac{dN_{\rm gal}}{dzd\Omega}$ [sr$^{-1}$]')
        ax2[0].set_ylim([10, 10 ** 9])
        ax2[1].set_ylabel(r'Completeness')
        ax2[1].set_xlabel(r'$z$')
        save_fig_redis(r,name,"numdensity",fig2)

        gal_overdensity = np.median(gcp + bgp, axis=1)

        expected_tot = cat.sch_fun.background_effective_galaxy_density(-np.inf * np.ones_like(zarr),
                                                                       zarr) * cosmo_ref.dVc_by_dzdOmega_at_z(zarr)
        fraction = gal_overdensity / expected_tot

        fig3 = plt.figure()
        plt.plot(zarr, fraction)
        plt.hlines(1, zarr.min(), zarr.max(), ls='--')
        plt.ylabel("Over(Under)density")
        plt.xlabel("z")

        save_fig_redis(r,name,"overunder",fig3)

        # For this check we will use NSBH injections from the R&P group
        data = h5py.File(r'/mnt/c/Users/Calvi/2025 IREU Sapienza/endo3_nsbhpop-LIGO-T2100113-v12.hdf5')
        cosmo_ref = icarogw.cosmology.astropycosmology(10)
        cosmo_ref.build_cosmology(FlatLambdaCDM(H0=69., Om0=0.3065))

        # We select the maximum IFAR among the searches
        ifarmax = np.vstack([data['injections'][key] for key in
                             ['ifar_cwb', 'ifar_gstlal', 'ifar_mbta', 'ifar_pycbc_bbh', 'ifar_pycbc_hyperbank']])
        ifarmax = np.max(ifarmax, axis=0)
        time_O3 = (28519200 / 86400) / 365  # Time of observation for O3 in tr

        # The prior for this injection set is saved in source frame
        prior = data['injections/mass1_source_mass2_source_sampling_pdf'][()] * data['injections/redshift_sampling_pdf'][()] / (
                    np.pi * 4)  # Add prior on sky angle (isotropic)
        prior *= icarogw.conversions.source2detector_jacobian(data['injections/redshift'][()],
                                                              cosmo_ref)  # Add jacobian to convert prior in detector frame

        # Prepare the input data
        injections_dict = {'mass_1': data['injections/mass1'][()], 'mass_2': data['injections/mass2'][()],
                           'luminosity_distance': data['injections/distance'][()],
                           'right_ascension': data['injections/right_ascension'][()],
                           'declination': data['injections/declination'][()]}

        # Initialize the injections as usual
        inj = icarogw.injections.injections(injections_dict, prior=prior, ntotal=data.attrs['total_generated'], Tobs=time_O3)

        # Select injections with IFAR higher than 4yr
        inj.update_cut(ifarmax >= 4)

        # Pixelize the injections
        inj.pixelize_with_catalog(cat)

        # Wrappers definition
        cosmo_wrap = icarogw.wrappers.FlatLambdaCDM_wrap(zmax=3.)
        rate_wrap = icarogw.wrappers.rateevolution_Madau()

        H0array = np.linspace(20, 140, 1000)
        posterior = np.zeros_like(H0array)

        # Rate definition
        rate_model = icarogw.rates.CBC_catalog_vanilla_rate_skymap(cat, cosmo_wrap, rate_wrap, scale_free=True)

        # Likelihood definition
        likelihood = icarogw.likelihood.hierarchical_likelihood(pos_cat, inj, rate_model, nparallel=Npar, neffINJ=None,
                                                                neffPE=NeffPE)
        try:
            for i, H0 in enumerate(H0array):
                likelihood.parameters = {'Om0': 0.308, 'gamma': 4.59, 'kappa': 2.86, 'zp': 2.47, 'H0': H0}
                posterior[i] = likelihood.log_likelihood()

            posterior -= posterior.max()
            posterior = np.exp(posterior)
            posterior /= np.trapz(posterior, H0array)

            H0array = np.linspace(20, 140, 1000)
            posterior_empty = np.zeros_like(H0array)
            # Rate definition
            rate_model = icarogw.rates.CBC_catalog_vanilla_rate_skymap(empty_cat, cosmo_wrap, rate_wrap, scale_free=True)

            # Likelihood definition
            likelihood = icarogw.likelihood.hierarchical_likelihood(pos_cat, inj, rate_model, nparallel=5096, neffINJ=None,
                                                                    neffPE=NeffPE)

            for i, H0 in enumerate(H0array):
                likelihood.parameters = {'Om0': 0.308, 'gamma': 4.59, 'kappa': 2.86, 'zp': 2.47, 'H0': H0}
                posterior_empty[i] = likelihood.log_likelihood()
            posterior_empty -= posterior_empty.max()
            posterior_empty = np.exp(posterior_empty)
            posterior_empty /= np.trapz(posterior_empty, H0array)

            fig4 = plt.figure()
            plt.plot(H0array, posterior, label='Glade+ K-band eps-1')
            plt.plot(H0array, posterior_empty, label='Empty catalog')
            plt.legend()
            plt.title(name)
            plt.ylim([0, 0.02])
            plt.xlabel(r'$H_0$[km/s/Mpc]')
            plt.ylabel('Posterior')
            plt.xlim([20, 140])
            save_fig_redis(r,name,"posterior plot",fig4)

            H0df = pd.DataFrame({
                'H0': H0array,
                'Posterior': posterior,
                'Empty': posterior_empty
            })
            H0_json = H0df.to_json()

            r.hset(name,"posterior",H0_json)
            plt.close()

        except:
            print("Couldn't draw from H0 posterior")
            r.hset(name, "status", "Analysis failed")
            raise Exception("Couldn't draw from H0 posterior")
            import traceback
            traceback.print_exc()
    except:
        print("analyze func never ran",flush=True)
        import traceback
        traceback.print_exc()