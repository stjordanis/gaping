import os
import gin
from tensorflow.python.platform import test
mock = test.mock
import numpy as np
import tensorflow as tf
import tensorflow.compat.v1 as tf1

from gaping import wrapper

from tensorflow.python.eager import context
from tensorflow.python.framework import ops

_cached_tpu_topology = None

class GapingTestCase(tf.test.TestCase):
  """Base class for test cases."""

  def __init__(self, *args, **kws):
    super().__init__(*args, **kws)
    self._cached_session = None

  def _ClearCachedSession(self):
    if self._cached_session is not None:
      self._cached_session.close()
      self._cached_session = None

  def session(self, graph=None, config=None):
    if graph is None:
      graph = ops.get_default_graph()
    session = wrapper.clone_session(self.cached_session(), graph=graph, config=config)
    return session

  @property
  def topology(self):
    return _cached_tpu_topology

  @topology.setter
  def topology(self, value):
    global _cached_tpu_topology
    _cached_tpu_topology = value

  def cached_session(self, interactive=False):
    if self._cached_session is None:
      self._cached_session = wrapper.create_session(interactive=interactive)
      if self.topology is None and 'TPU_NAME' in os.environ:
        # Get the TPU topology.
        self.topology = wrapper.get_topology(force=bool(int(os.getenv('TPU_INIT', '0'))))
    return self._cached_session

  def evaluate(self, tensors, **kws):
    """Evaluates tensors and returns numpy values.

    Args:
      tensors: A Tensor or a nested list/tuple of Tensors.

    Returns:
      tensors numpy values.
    """
    if context.executing_eagerly():
      raise NotImplementedError()
      #return self._eval_helper(tensors)
    else:
      sess = ops.get_default_session()
      if sess is None:
        with self.session() as sess:
          return sess.run(tensors, **kws)
      else:
        return sess.run(tensors, **kws)

  def log(self, message, *args, **kws):
    tf1.logging.info(message, *args, **kws)

  def bucket_path(self, *parts):
    base = os.environ.get('MODEL_BUCKET') or os.environ['TPU_BUCKET']
    return os.path.join(base, *parts)

  def setUp(self):
    super().setUp()
    # Create the cached session.
    self.cached_session()
    # Clear the gin cofiguration.
    gin.clear_config()

