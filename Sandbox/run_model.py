import numpy as np
import arviz as az
import matplotlib.pyplot as plt
import pymc3 as pm


def run_price_trend_model(pricedata):
    with pm.Model() as trend_model:
        scaling_factor = 1
        X = np.array(list(map(lambda p: p * scaling_factor, range(0, len(pricedata)))))
        observed_prices = np.array(list(map(lambda p: p.value * scaling_factor, pricedata)))

        # stdev = pm.HalfNormal('stdev', sd=1)
        # intercept = pm.Normal('intercept', mu=2.3, sd=1)
        intercept = 1 * scaling_factor
        coeff = pm.Normal('beta', mu=0.01, sd=0.1)

        expected_price = X * coeff + intercept
        prices = pm.Normal('prices', mu=expected_price, observed=observed_prices)

        samples = pm.sample(1000, cores=1)

        pm.traceplot(samples)
        plt.show()
        print(pm.summary(samples, kind="stats"))


def run_wage_correlation_model(pricedata, wages):
    with pm.Model() as wage_to_price_model:
        scale = 1
        X = np.array(list(map(lambda p: p.value * scale, wages)))
        observed_prices = np.array(list(map(lambda p: p.value * scale, pricedata)))

        intercept = pm.Normal('intercept', mu=-2.7, sd=0.5)
        coeff = pm.Normal('beta', mu=3.7, sd=0.5)

        expected_price = X * coeff + intercept
        prices = pm.Normal('prices', mu=expected_price, observed=observed_prices)

        samples = pm.sample(1000, cores=1)

        pm.traceplot(samples)
        plt.show()
        print(pm.summary(samples, kind="stats"))


def run_breakpoint_model(prices):
    with pm.Model() as trend_change_model:
        scaling_factor = 10
        relative_changes = list(map(lambda p: p.value * scaling_factor, prices))
        dates = list(map(lambda p: p.date, prices))

        relative_changes_np = np.array(relative_changes)
        date_indexes = np.arange(0, len(prices))

        # Prior distributions
        trend_change_point = pm.Cauchy('changepoint', alpha=100, beta=2)
        early_trend = pm.Normal('early_trend', mu=0.1, sd=0.1)
        late_trend = pm.Normal('late_trend', mu=-0.05, sd=0.1)

        # Transformed variable
        trend = pm.math.switch(trend_change_point >= date_indexes, early_trend, late_trend)

        # Likelyhood
        price_change = pm.Normal('price_change', trend, observed=relative_changes_np)

        samples = pm.sample(draws=1000, tune=1000, cores=1)

        # az.plot_trace(samples, var_names=['changepoint', 'early_trend', 'late_trend'])
        # trend_change_model.early_trend.summary()#
        # trend_change_model.trace['early_trend']

        pm.traceplot(samples)
        plt.show()
        print(pm.summary(samples, kind="stats"))


def run_model():
    print(f"Running on PyMC3 v{pm.__version__}")
    # Initialize random number generator
    RANDOM_SEED = 8927
    np.random.seed(RANDOM_SEED)
    az.style.use("arviz-darkgrid")

    # True parameter values
    alpha, sigma = 1, 1
    beta = [1, 2.5]

    # Size of dataset
    size = 100

    # Predictor variable
    X1 = np.random.randn(size)
    X2 = np.random.randn(size) * 0.2

    # Simulate outcome variable
    Y = alpha + beta[0] * X1 + beta[1] * X2 + np.random.randn(size) * sigma

    fig, axes = plt.subplots(1, 2, sharex=True, figsize=(10, 4))
    axes[0].scatter(X1, Y, alpha=0.6)
    axes[1].scatter(X2, Y, alpha=0.6)
    axes[0].set_ylabel("Y")
    axes[0].set_xlabel("X9")
    axes[1].set_xlabel("X9");

    # print (matplotlib.rcParams['backend'])

    basic_model = pm.Model()

    with basic_model:
        # Priors for unknown model parameters
        alpha = pm.Normal("alpha", mu=0, sigma=10)
        beta = pm.Normal("beta", mu=0, sigma=10, shape=2)
        sigma = pm.HalfNormal("sigma", sigma=1)

        # Expected value of outcome
        mu = alpha + beta[0] * X1 + beta[1] * X2

        # Likelihood (sampling distribution) of observations
        Y_obs = pm.Normal("Y_obs", mu=mu, sigma=sigma, observed=Y)

    plt.show()
    print("Plotting done")
