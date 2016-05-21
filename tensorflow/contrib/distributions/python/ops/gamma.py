# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""The Gamma distribution class."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tensorflow.contrib.distributions.python.ops.distribution import ContinuousDistribution  # pylint: disable=line-too-long
from tensorflow.contrib.framework.python.framework import tensor_util as contrib_tensor_util  # pylint: disable=line-too-long
from tensorflow.python.framework import ops
from tensorflow.python.framework import tensor_shape
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import check_ops
from tensorflow.python.ops import constant_op
from tensorflow.python.ops import control_flow_ops
from tensorflow.python.ops import math_ops


class Gamma(ContinuousDistribution):
  """The `Gamma` distribution with parameter alpha and beta.

  The parameters are the shape and inverse scale parameters alpha, beta.

  The PDF of this distribution is:

  ```pdf(x) = (beta^alpha)(x^(alpha-1))e^(-x*beta)/Gamma(alpha), x > 0```

  and the CDF of this distribution is:

  ```cdf(x) =  GammaInc(alpha, beta * x) / Gamma(alpha), x > 0```

  where GammaInc is the incomplete lower Gamma function.

  Examples:

  ```python
  dist = Gamma(alpha=3.0, beta=2.0)
  dist2 = Gamma(alpha=[3.0, 4.0], beta=[2.0, 3.0])
  ```

  """

  def __init__(self, alpha, beta, name="Gamma"):
    """Construct Gamma distributions with parameters `alpha` and `beta`.

    The parameters `alpha` and `beta` must be shaped in a way that supports
    broadcasting (e.g. `alpha + beta` is a valid operation).

    Args:
      alpha: `float` or `double` tensor, the shape params of the
        distribution(s).
        alpha must contain only positive values.
      beta: `float` or `double` tensor, the inverse scale params of the
        distribution(s).
        beta must contain only positive values.
      name: The name to give Ops created by the initializer.

    Raises:
      TypeError: if `alpha` and `beta` are different dtypes.
    """
    with ops.op_scope([alpha, beta], name):
      alpha = ops.convert_to_tensor(alpha, name="alpha_before_dependencies")
      beta = ops.convert_to_tensor(beta, name="beta_before_dependencies")
      contrib_tensor_util.assert_same_float_dtype((alpha, beta))
      with ops.control_dependencies([
          check_ops.assert_positive(alpha), check_ops.assert_positive(beta)
      ]):
        self._alpha = alpha
        self._beta = beta
        self._name = name

    with ops.op_scope([self._alpha, self._beta], name, "mean"):
      self._mean = self._alpha / self._beta
      self._batch_shape = self._mean.get_shape()

    with ops.op_scope([self._alpha, self._beta], name, "variance"):
      self._variance = self._alpha / math_ops.square(self._beta)

    self._event_shape = tensor_shape.TensorShape([])

  @property
  def name(self):
    return self._name

  @property
  def dtype(self):
    return self._alpha.dtype

  @property
  def alpha(self):
    return self._alpha

  @property
  def beta(self):
    return self._beta

  def batch_shape(self, name="batch_shape"):
    with ops.name_scope(self.name):
      return array_ops.shape(self._mean, name=name)

  def get_batch_shape(self):
    return self._batch_shape

  def event_shape(self, name="event_shape"):
    with ops.name_scope(self.name):
      return constant_op.constant(1, name=name)

  def get_event_shape(self):
    return self._event_shape

  @property
  def mean(self):
    return self._mean

  @property
  def variance(self):
    return self._variance

  def log_pdf(self, x, name="log_pdf"):
    """Log pdf of observations in `x` under these Gamma distribution(s).

    Args:
      x: tensor of dtype `dtype`, must be broadcastable with `alpha` and `beta`.
      name: The name to give this op.

    Returns:
      log_pdf: tensor of dtype `dtype`, the log-PDFs of `x`.
    Raises:
      TypeError: if `x` and `alpha` are different dtypes.
    """
    with ops.op_scope([self._alpha, self._beta, x], self.name):
      with ops.name_scope(name):
        alpha = self._alpha
        beta = self._beta
        x = ops.convert_to_tensor(x)
        x = control_flow_ops.with_dependencies(
            [check_ops.assert_positive(x)], x)
        contrib_tensor_util.assert_same_float_dtype(tensors=[x,],
                                                    dtype=self.dtype)

        return (alpha * math_ops.log(beta) + (alpha - 1) * math_ops.log(x) -
                beta * x - math_ops.lgamma(self._alpha))

  def pdf(self, x, name="pdf"):
    with ops.name_scope(name):
      return math_ops.exp(self.log_pdf(x, name))

  def log_cdf(self, x, name="log_cdf"):
    """Log CDF of observations `x` under these Gamma distribution(s).

    Args:
      x: tensor of dtype `dtype`, must be broadcastable with `alpha` and `beta`.
      name: The name to give this op.

    Returns:
      log_cdf: tensor of dtype `dtype`, the log-CDFs of `x`.
    """
    with ops.op_scope([self._alpha, self._beta, x], self.name):
      with ops.name_scope(name):
        x = ops.convert_to_tensor(x)
        x = control_flow_ops.with_dependencies(
            [check_ops.assert_positive(x)], x)
        contrib_tensor_util.assert_same_float_dtype(tensors=[x,],
                                                    dtype=self.dtype)
        # Note that igamma returns the regularized incomplete gamma function,
        # which is what we want for the CDF.
        return math_ops.log(math_ops.igamma(self._alpha, self._beta * x))

  def cdf(self, x, name="cdf"):
    with ops.op_scope([self._alpha, self._beta, x], self.name):
      with ops.name_scope(name):
        return math_ops.igamma(self._alpha, self._beta * x)

  def entropy(self, name="entropy"):
    """The entropy of Gamma distribution(s).

    This is defined to be

    ```entropy = alpha - log(beta) + log(Gamma(alpha))
                 + (1-alpha)digamma(alpha)```

    where digamma(alpha) is the digamma function.

    Args:
      name: The name to give this op.

    Returns:
      entropy: tensor of dtype `dtype`, the entropy.
    """
    with ops.op_scope([self.alpha, self._beta], self.name):
      with ops.name_scope(name):
        alpha = self._alpha
        beta = self._beta
        return (alpha - math_ops.log(beta) + math_ops.lgamma(alpha) +
                (1 - alpha) * math_ops.digamma(alpha))

  @property
  def is_reparameterized(self):
    return False
