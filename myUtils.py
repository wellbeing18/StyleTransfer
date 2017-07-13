# -*- coding: utf-8 -*-
import tensorflow as tf
from tensorflow.python.framework import ops
import numpy as np
import functools


def lazy_property(func):
    attribute = '_lazy_' + func.__name__

    @property
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attribute):
            setattr(self, attribute, func(self))
        return getattr(self, attribute)
    return wrapper


# 若bias_shape 为 None，表示不使用bias
def resize_conv(inputs, kernel_shape, bias_shape, strides, w_i, b_i=None, activation=tf.nn.relu):
    height = tf.shape(inputs)[1]
    width = tf.shape(inputs)[2]
    target_height = height * strides[1] * 2
    target_width = width * strides[1] * 2
    resized = tf.image.resize_images(inputs,
                                     size=[target_height, target_width],
                                     method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
    return conv(resized, kernel_shape, bias_shape, strides, w_i, b_i, activation)


def instance_norm(inputs):
    epsilon = 1e-9  # 避免0除数
    mean, var = tf.nn.moments(inputs, [1, 2], keep_dims=True)
    return tf.div(inputs - mean, tf.sqrt(tf.add(var, epsilon)))


def residual(inputs, kernel_shape, bias_shape, strides, w_i, b_i=None):
    tmp = conv(inputs, kernel_shape, bias_shape, strides, w_i, b_i)
    with tf.variable_scope('residual'):
        return inputs + conv(tmp, kernel_shape, bias_shape, strides, w_i, b_i)


def conv(inputs, kernel_shape, bias_shape, strides, w_i, b_i=None, activation=tf.nn.relu):
    # 使用tf.layers
    # relu1 = tf.layers.conv2d(input_imgs, filters=24, kernel_size=[5, 5], strides=[2, 2],
    #                          padding='SAME', activation=tf.nn.relu,
    #                          kernel_initializer=w_i, bias_initializer=b_i)
    weights = tf.get_variable('weights', shape=kernel_shape, initializer=w_i)
    conv = tf.nn.conv2d(inputs, weights, strides=strides, padding='SAME')
    if bias_shape is not None:
        biases = tf.get_variable('biases', shape=bias_shape, initializer=b_i)
        return activation(conv + biases) if activation is not None else conv + biases
    return activation(conv) if activation is not None else conv


# 默认有bias，激活函数为relu
def dense(inputs, units, bias_shape, w_i, b_i=None, activation=tf.nn.relu):
    # 使用tf.layers，注意：先flatten
    # dense1 = tf.layers.dense(tf.contrib.layers.flatten(relu5), activation=tf.nn.relu, units=50)
    if not isinstance(inputs, ops.Tensor):
        inputs = ops.convert_to_tensor(inputs, dtype='float')
        # dim_list = inputs.get_shape().as_list()
        # flatten_shape = dim_list[1] if len(dim_list) <= 2 else reduce(lambda x, y: x * y, dim_list[1:])
        # reshaped = tf.reshape(inputs, [dim_list[0], flatten_shape])
    if len(inputs.shape) > 2:
        inputs = tf.contrib.layers.flatten(inputs)
    flatten_shape = inputs.shape[1]
    weights = tf.get_variable('weights', shape=[flatten_shape, units], initializer=w_i)
    dense = tf.matmul(inputs, weights)
    if bias_shape is not None:
        biases = tf.get_variable('biases', shape=[units], initializer=b_i)
        return activation(dense + biases) if activation is not None else dense + biases
    return activation(dense) if activation is not None else dense


def flatten(inputs):
    # 使用tf.layers
    # return tf.contrib.layers.flatten(inputs)
    return tf.reshape(inputs, [-1, np.prod(inputs.get_shape().as_list()[1:])])
    # flatten = tf.reshape(relu5, [-1, np.prod(relu5.shape.as_list()[1:])])



