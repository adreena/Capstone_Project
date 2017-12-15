from styx_msgs.msg import TrafficLight

import tensorflow as tf
from PIL import Image
from keras.models import  load_model
import numpy as np
import os
import uuid

class TLClassifier(object):
    def __init__(self, traffic_light_model_path, ssd_model_path, save_path):
        #TODO load classifier
        # path1 = './rfcn_resnet101_coco_2017_11_08/frozen_inference_graph.pb'
        #path = './src/tl_detector/light_classification/ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb'
        self.save_path = save_path
        self.sess_ssd, self.base_ops_ssd = self.load_graph(ssd_model_path)

        self.traffic_light_model_path = traffic_light_model_path
        self.sess_tl, self.base_ops_tl = self.load_graph(traffic_light_model_path)

        # x = tf.placeholder(tf.float32, (None, 32, 32, 3))
        # y = tf.placeholder(tf.int32, (None))




    def load_graph(self, graph_file, use_xla=False):
        jit_level = 0
        config = tf.ConfigProto()
        if use_xla:
            jit_level = tf.OptimizerOptions.ON_1
            config.graph_options.optimizer_options.global_jit_level = jit_level

        with tf.Session(graph=tf.Graph(), config=config) as sess:
            gd = tf.GraphDef()
            with tf.gfile.Open(graph_file, 'rb') as f:
                data = f.read()
                gd.ParseFromString(data)
            tf.import_graph_def(gd, name='')
            ops = sess.graph.get_operations()
            n_ops = len(ops)
        return sess, ops

    def find_traffic_light_boxes(self,image):
        lights = []
        RESIZE = 32
        graph=self.sess_ssd.graph
        with tf.Session() as session:
            image_tensor = graph.get_tensor_by_name('image_tensor:0')
            detection_boxes = graph.get_tensor_by_name('detection_boxes:0')
            detection_classes = graph.get_tensor_by_name('detection_classes:0')
            num_detections = graph.get_tensor_by_name('num_detections:0')
            detection_scores = graph.get_tensor_by_name('detection_scores:0')

            image_np_expanded = np.expand_dims(image, axis=0)

            # Actual detection.
            (boxes, scores, classes, num) = self.sess_ssd.run([detection_boxes, detection_scores, detection_classes, num_detections],
              feed_dict={image_tensor: image_np_expanded})

            boxes = np.squeeze(boxes)
            scores = np.squeeze(scores)
            classes = np.squeeze(classes).astype(np.int32)
            min_score_thresh = .50
            TRAFFIC_LIGHT_INDEX = 10

            image_pillow =  Image.fromarray(image)
            im_height,im_width = image_pillow.size

            image_cropped = None
            # image_pillow.save('{}/{}.png'.format(self.save_path,uuid.uuid4().hex))
            traffic_found = False
            i=0
            if boxes is not None:
                for i in range(boxes.shape[0]):
                    if (scores is None or scores[i] > min_score_thresh) and classes[i] == TRAFFIC_LIGHT_INDEX:
                        (left, right, top, bottom) = (boxes[i][0] * im_width, boxes[i][2] * im_width, boxes[i][1] * im_height, boxes[i][3] * im_height)
                        image_cropped = image_pillow.crop((top, left,bottom,right ))
                        lights.append(np.asarray(image_cropped.resize((RESIZE,RESIZE))))
                        # image_cropped.save('{}/{}-{}-{}.png'.format(self.save_path,classes[i],dist,uuid.uuid4().hex))
        return lights

    def classify_traffic_light(self, lights):
        light_votes = {TrafficLight.RED:0, TrafficLight.YELLOW:0, TrafficLight.GREEN:0}
        X_lights= np.array(lights)

        graph=self.sess_tl.graph
        with tf.Session() as session:
            x = graph.get_tensor_by_name('x:0')
            y = graph.get_tensor_by_name('y:0')
            drop_out = graph.get_tensor_by_name('drop_out:0')
            logits = graph.get_tensor_by_name('logits:0')
            predict_op = tf.argmax(logits,1)
            predictions = self.sess_tl.run(predict_op, feed_dict={x: X_lights, drop_out:1})
            # print(light_to_car_distance)
            for pred in predictions:
                # predictions.append(lights[y])
                if pred == 0:
                    light_votes[TrafficLight.RED] +=1
                elif pred == 1:
                    light_votes[TrafficLight.YELLOW] +=1
                elif pred == 2:
                    light_votes[TrafficLight.GREEN] +=1
        return light_votes

    def find_traffic_light_color(self,image, dist):

        color_label = TrafficLight.UNKNOWN

        lights = self.find_traffic_light_boxes(image)
        if len(lights)>0:
            light_votes = self.classify_traffic_light(lights)
            max_score = 0
            for key,val in light_votes.items():
                if val > max_score:
                    color_label = key
            return color_label
        else:
            return TrafficLight.UNKNOWN


    def get_classification(self, image, dist):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        #TODO implement light color prediction
        # ssd call
        # bbox crop
        # test to keras model
        color_label = self.find_traffic_light_color(image, dist)

        return color_label
