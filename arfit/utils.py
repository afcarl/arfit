from pylab import *
import pspec as ps
import bz2
import emcee 
import os
import os.path as op
import pickle
import plotutils.autocorr as ac
import plotutils.plotutils as pu
import plotutils.runner as pr
import scipy.stats as ss
import triangle as tri

def plot_psd(runner, xlabel=None, ylabel=None, Npts=1000, Nmcmc=1000, oversampling=5, nyquist_factor=3):
    logpost = runner.sampler.logp.lp
    chain = runner.burnedin_chain[0,...].reshape((-1, runner.chain.shape[3]))
    
    fs, ls = ps.normalised_lombscargle(logpost.t, logpost.y, logpost.dy, oversampling=oversampling, nyquist_factor=nyquist_factor)

    psds = []
    wns = []
    for p in permutation(chain)[:Nmcmc,:]:
        psds.append(logpost.power_spectrum(fs, p))
        try:
            wns.append(logpost.white_noise(p, np.max(fs) - np.min(fs)))
        except:
            pass
    psds = array(psds)
    wns = array(wns)
    ar_psds = psds
    try:
        psds = wns.reshape((-1, 1)) + psds
    except:
        pass

    loglog(fs, ls, '-k')
    
    loglog(fs, median(psds, axis=0), '-b')
    fill_between(fs, percentile(psds, 84, axis=0), percentile(psds, 16, axis=0), color='b', alpha=0.25)
    fill_between(fs, percentile(psds, 97.5, axis=0), percentile(psds, 2.5, axis=0), color='b', alpha=0.25)
    
    loglog(fs, median(ar_psds, axis=0), '-r')
    fill_between(fs, percentile(ar_psds, 84, axis=0), percentile(ar_psds, 16, axis=0), color='r', alpha=0.25)
    fill_between(fs, percentile(ar_psds, 97.5, axis=0), percentile(ar_psds, 2.5, axis=0), color='r', alpha=0.25)
    try:
        plot(fs, 0*fs + median(wns), color='g')
        fill_between(fs, percentile(wns, 84) + 0*fs, percentile(wns, 16) + 0*fs, color='g', alpha=0.25)
        fill_between(fs, percentile(wns, 97.5) + 0*fs, percentile(wns, 2.5) + 0*fs, color='g', alpha=0.25)
    except:
        pass
    
    axis(ymin=np.min(ls)/1000.0)

    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)

def plot_residuals(runner, Nmcmc=1000, Npts=1000):
    logpost = runner.sampler.logp.lp
    resid = []
    for p in permutation(runner.burnedin_chain[0,...].reshape((-1, logpost.nparams)))[:Nmcmc, :]:
        resid.append(logpost.standardised_residuals(p))
    resid = array(resid)
    errorbar(logpost.t, mean(resid, axis=0), yerr=std(resid, axis=0), color='k', fmt='.')

def plot_resid_distribution(runner, N=10, Npts=1000):
    logpost = runner.sampler.logp.lp
    for p in permutation(runner.burnedin_chain[0,...].reshape((-1, logpost.nparams)))[:N, :]:
        r = logpost.standardised_residuals(p)
        pu.plot_kde_posterior(r, color='b', alpha=0.1)
    xs = linspace(-5, 5, Npts)
    plot(xs, ss.norm.pdf(xs), '-k')

def plot_resid_acf(runner, N=10):
    logpost = runner.sampler.logp.lp
    for p in permutation(runner.burnedin_chain[0,...].reshape((-1, logpost.nparams)))[:N,:]:
        r = logpost.standardised_residuals(p)
        acorr(r, maxlags=None, alpha=0.1)

    axhline(1.96/sqrt(r.shape[0]), color='b')
    axhline(-1.96/sqrt(r.shape[0]), color='b')

def plot_evidence_integrand(runner, fburnin=0.5):
    istart = int(round(fburnin*runner.chain.shape[2]))

    lnlikes = runner.lnlikelihood[:, :, istart:]
    mean_lnlikes = np.mean(lnlikes, axis=(1,2))

    mean_lnlikes = mean_lnlikes[:-1] # strip off beta=0
    betas = runner.sampler.betas[:-1] # strip off beta=0
    
    plot(betas, betas*mean_lnlikes)
    xlabel(r'$\beta$')
    ylabel(r'$\beta \left\langle \ln \mathcal{L} \right\rangle_\beta$')
    xscale('log')

def process_output_dir(dir, runner=None, return_runner=False):
    if runner is None:
        with bz2.BZ2File(op.join(dir, 'runner.pkl.bz2'), 'r') as inp:
            runner = pickle.load(inp)

    runner.sampler.logp.lp._mean_variance()

    figure()
    loglog(1/runner.sampler.beta_history.T)
    axvline(runner.sampler.chain.shape[2]*0.2)
    savefig(op.join(dir, 'temp-history.pdf'))
    
    figure()
    pu.plot_emcee_chains_one_fig(runner.burnedin_chain[0,...])
    savefig(op.join(dir, 'chains.pdf'))

    figure()
    plot_psd(runner.logp.lp, runner.burnedin_chain[0,...].reshape((-1, runner.chain.shape[-1])))
    savefig(op.join(dir, 'psd.pdf'))

    figure()
    plot_residuals(runner)
    savefig(op.join(dir, 'resid.pdf'))

    figure()
    plot_resid_distribution(runner)
    savefig(op.join(dir, 'resid-distr.pdf'))

    if return_runner:
        return runner
