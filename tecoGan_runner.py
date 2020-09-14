# from unittest import runner
# import os, math, time, collections, numpy as np
import numpy as np
import os, time, numpy as np
import tensorflow as tf
from tensorflow.python.util import deprecation
import random as rn
# import sys, shutil, subprocess

from ThirdParty.TecoGAN.lib.ops import *
# from ThirdParty.TecoGAN.lib.dataloader import inference_data_loader, frvsr_gpu_data_loader
from ThirdParty.TecoGAN.lib.dataloader import inference_data_loader
from ThirdParty.TecoGAN.lib.frvsr import generator_F, fnet
# from ThirdParty.TecoGAN.lib.Teco import FRVSR, TecoGAN

from pathlib import Path
from numba import cuda

# fix all randomness, except for multi-treading or GPU process
import tensorflow.contrib.slim as slim
class TecoGANRunner:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    deprecation._PRINT_DEPRECATION_WARNINGS = False
    os.environ['PYTHONHASHSEED'] = '0'
    np.random.seed(42)
    rn.seed(12345)
    tf.compat.v1.set_random_seed(1234)

    def RunTeco(self, input_dir, output_dir):

        # Declare the test data reader
        # inference_data = inference_data_loader('./LR/bomb/')
        inference_data = inference_data_loader(input_dir)
        input_shape = [1,] + list(inference_data.inputs[0].shape)
        output_shape = [1,input_shape[1]*4, input_shape[2]*4, 3]
        oh = input_shape[1] - input_shape[1]//8 * 8
        ow = input_shape[2] - input_shape[2]//8 * 8
        paddings = tf.constant([[0,0], [0,oh], [0,ow], [0,0]])
        print("input shape:", input_shape)
        print("output shape:", output_shape)
        
        # build the graph
        inputs_raw = tf.compat.v1.placeholder(tf.float32, shape=input_shape, name='inputs_raw')
        
        pre_inputs = tf.Variable(tf.zeros(input_shape), trainable=False, name='pre_inputs')
        pre_gen = tf.Variable(tf.zeros(output_shape), trainable=False, name='pre_gen')
        pre_warp = tf.Variable(tf.zeros(output_shape), trainable=False, name='pre_warp')
        
        transpose_pre = tf.compat.v1.space_to_depth(pre_warp, 4)
        inputs_all = tf.concat( (inputs_raw, transpose_pre), axis = -1)
        with tf.compat.v1.variable_scope('generator'):
            # gen_output = generator_F(inputs_all, 3, reuse=False, FLAGS=FLAGS)
            gen_output = generator_F(inputs_all, 3, reuse=False)
            # Deprocess the images outputed from the model, and assign things for next frame
            with tf.compat.v1.control_dependencies([ tf.compat.v1.assign(pre_inputs, inputs_raw)]):
                outputs = tf.compat.v1.assign(pre_gen, deprocess(gen_output))
        
        inputs_frames = tf.concat( (pre_inputs, inputs_raw), axis = -1)
        with tf.variable_scope('fnet'):
            gen_flow_lr = fnet( inputs_frames, reuse=False)
            gen_flow_lr = tf.pad(gen_flow_lr, paddings, "SYMMETRIC") 
            gen_flow = upscale_four(gen_flow_lr*4.0)
            gen_flow.set_shape( output_shape[:-1]+[2] )
        pre_warp_hi = tf.contrib.image.dense_image_warp(pre_gen, gen_flow)
        before_ops = tf.compat.v1.assign(pre_warp, pre_warp_hi)

        print('Finish building the network')
        
        # In inference time, we only need to restore the weight of the generator
        var_list = tf.compat.v1.get_collection(tf.compat.v1.GraphKeys.MODEL_VARIABLES, scope='generator')
        var_list = var_list + tf.compat.v1.get_collection(tf.compat.v1.GraphKeys.MODEL_VARIABLES, scope='fnet')
        
        weight_initiallizer = tf.compat.v1.train.Saver(var_list)
        
        # Define the initialization operation
        init_op = tf.compat.v1.global_variables_initializer()
        local_init_op = tf.compat.v1.local_variables_initializer()

        config = tf.compat.v1.ConfigProto()
        config.gpu_options.allow_growth = True
        output_ext = 'png'
        checkpoint = '.\\final-model\\TecoGAN'
        self.sess = None
        with tf.compat.v1.Session(config=config) as sess1:
            self.sess = sess1
            # Load the pretrained model
            self.sess.run(init_op)
            self.sess.run(local_init_op)
            
            print('Loading weights from ckpt model')
            weight_initiallizer.restore(self.sess, checkpoint)
            max_iter = len(inference_data.inputs)
                    
            srtime = 0
            print('Frame evaluation starts!!')
            for i in range(max_iter):
                input_im = np.array([inference_data.inputs[i]]).astype(np.float32)
                feed_dict={inputs_raw: input_im}
                t0 = time.time()
                if(i != 0):
                    self.sess.run(before_ops, feed_dict=feed_dict)
                output_frame = self.sess.run(outputs, feed_dict=feed_dict)
                srtime += time.time()-t0
                
                if(i >= 5): 
                    name, _ = os.path.splitext(os.path.basename(str(inference_data.paths_LR[i])))
                    filename = name
                    print('saving image %s' % filename)
                    out_path = str(Path(output_dir) / str(filename)) +'.'+ output_ext
                    print(out_path)
                    save_img(out_path, output_frame[0])
                else:# First 5 is a hard-coded symmetric frame padding, ignored but time added!
                    print("Warming up %d"%(5-i))
            self.sess.close()
        print( "total time " + str(srtime) + ", frame number " + str(max_iter) )
        # cuda.select_device(0)
        # cuda.close()
        # device = cuda.get_current_device()
        # cuda.
        # cuda.reset()
# if __name__ == "__main__":
#     run = TecoGANRunner()
#     run.RunTeco()