---
title: "COVID-19 Predictors"
subtitle: "university project, two repos"
date: 2021-10-12
featured: false
summary: "Two coursework predictors for COVID-19 case trends — a neural network compared against ARIMA and Prophet in one, a scikit-learn regression model reframed as OHLC-style candles in the other."
---

Two related but separate submissions for the same coursework, tackling COVID-19 case-count prediction from two different angles.

## Neural network vs. ARIMA vs. Prophet ([AI-Covid19](https://github.com/Petrickah/AI-Covid19))

Built with TensorFlow and Keras, this one trains an artificial neural network on a moving window extracted from the case-count time series, with values normalized per 1000 people using day-over-day differences. An Autoregressive Moving Average step turns those windows into weekly averages, which the model then uses to predict up to 7 days out.

The finding worth remembering: a single-layer network could pick up the general trend but not much precision. Two layers hit the sweet spot — accurate without overfitting. Adding more layers past that made things worse, not better — the model started overfitting instead of improving.

## Regression, framed as candlesticks ([ML-Covid19](https://github.com/Petrickah/ML-Covid19))

Built with Pandas and scikit-learn, this one reframes the same kind of time series as a finance-style OHLC (open/high/low/close) chart — each week's starting value, ending value, and min/max become the four numbers a candlestick chart would use. The prediction target: what value does the next week open at, given the current one?

Linear regression was the baseline; Polynomial regression and ElasticNet were compared against it. Polynomial regression won, scoring 98.6% on the test set.
