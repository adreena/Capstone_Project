import tensorflow as tf
import os
import csv
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
import boto3
from PIL import Image
import io
from tensorflow.contrib.layers import flatten
s3 = boto3.resource('s3')
bucket = 'capstone-trafficlights'
classes = ['Red', 'Yellow', 'Green']
num_classes =3
resize = 32

filter_depth_c1 = 6
filter_depth_c2 = 16
mu = 0
sigma = 0.1

weights = {
    'c1':tf.Variable(tf.truncated_normal(shape=(5, 5, 3, filter_depth_c1), mean = mu, stddev = sigma), name='weights_c1'),
    'c2':tf.Variable(tf.truncated_normal(shape=(5,5,6, filter_depth_c2), mean = mu, stddev = sigma), name='weights_c2'),
    'f1':tf.Variable(tf.truncated_normal(shape=(400, 120), mean = mu, stddev = sigma), name="weights_f1"),
    'f2':tf.Variable(tf.truncated_normal(shape=(120,84), mean = mu, stddev = sigma), name="weights_f2"),
    'output':tf.Variable(tf.truncated_normal(shape=(84,num_classes)), name="weight_output")
}
biases = {
    'c1':tf.Variable(tf.zeros(filter_depth_c1), name="bias_c1"),
    'c2':tf.Variable(tf.zeros(filter_depth_c2), name="bias_c2"),
    'f1':tf.Variable(tf.zeros(120),name="bias_f1"),
    'f2':tf.Variable(tf.zeros(84), name="bias_f2"),
    'output':tf.Variable(tf.zeros(num_classes), name="bias_output")
}

def conv2d(input,weights, bias):
    c = tf.nn.conv2d(input, weights, strides=[1,1,1,1], padding='VALID')
    c = tf.nn.bias_add(c,bias)
    c = tf.nn.relu(c)
    c = tf.nn.max_pool(c, ksize=[1,2,2,1], strides=[1,2,2,1], padding='VALID')
    return c

def fully_connected(x, weights, bias):
    f = tf.add(tf.matmul(x, weights), bias)
    f = tf.nn.relu(f)
    f = tf.nn.dropout(f, drop_out)
    return f

def model(x):

    #convnet1 32x32x3 -> 14x14x6
    conv1 = conv2d(x, weights['c1'], biases['c1'])

    #convnet2 14x14x6 -> 5x5x16
    conv2 = conv2d(conv1, weights['c2'], biases['c2'])

    #fully_connected 120 nodes
    conv2_flat = flatten(conv2)
    f1 = fully_connected(conv2_flat, weights['f1'], biases['f1'])

    # fully_connected 84 nodes
    f2 = fully_connected(f1, weights['f2'], biases['f2'])

    #output 3 nodes
    logits = tf.add(tf.matmul(f2,weights['output']), biases['output'], name="logits")

    return (conv1,conv2, f1, f2, logits)


def evaluate(data, val_generator):
    num_examples = len(data)
    total_accuracy = 0
    sess = tf.get_default_session()
    for X_batch, y_batch in val_generator:
        batch_accuracy = sess.run(accuracy, feed_dict={x: X_batch, y: y_batch, drop_out: 1})
        print(batch_accuracy, len(X_batch))
        total_accuracy += (batch_accuracy * len(X_batch))
    return total_accuracy / num_examples

from sklearn.utils import shuffle

def load_data_from_s3(path):
    data =[]

    with open('./src/tl_detector/light_classification/traffic_light_classifier/csv_classes.csv') as csvfile:
        reader = csv.reader(csvfile)
        line_count = 0
        for line in reader:
            if line_count>0:
                image = line[0]
                color = line[1]
                data.append(([image,color]))

            line_count+=1
    return data

def get_image(bucket,sample,resize):
    try:
        key= sample[0]
        image_obj = s3.Object(bucket, key)
        image = io.BytesIO(image_obj.get()['Body'].read())
        image = np.asarray(Image.open(image).resize((resize,resize)))
#         image= np.asarray( Image.open(image), dtype="int32" )
        return image
    except Exception as err:
        print(err)

def generator(bucket,samples,n_classes, batch_size = 64, resize=32):
    # while True:
    for offset in range(0,len(samples), batch_size):
        start = offset
        end = offset+batch_size
        if end > len(samples):
            end = len(samples)-1
        batch_sample = samples[start:end]
        images=[]
        colors=[]
        print("start:{} , end:{}".format(start, end ))
        for sample in batch_sample:
            #get images
            image = get_image(bucket, sample, resize)
            images.append(image)
            colors.extend(sample[1])

        x = np.array(images)
        y = np.array(colors)
        yield shuffle(x,y)

x = tf.placeholder(tf.float32, (None, 32,32,3), name="x")
y = tf.placeholder(tf.int32, (None), name="y")
drop_out = tf.placeholder(tf.float32, name="drop_out")
one_hot_y = tf.one_hot(y, num_classes, name="y_hat")
learning_rate = 0.0001
conv1, conv2, f1,f2 , logits = model(x)
predict_op = tf.argmax(logits,1)

tf.add_to_collection(x.name, x)
tf.add_to_collection(y.name, y)
tf.add_to_collection(drop_out.name, drop_out)

cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=one_hot_y)
cost = tf.reduce_mean(cross_entropy)
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
is_correct = tf.equal(tf.argmax(logits,1), tf.argmax(one_hot_y,1))
accuracy = tf.reduce_mean(tf.cast(is_correct, tf.float32))

def start():


    saver = tf.train.Saver()

    data = load_data_from_s3(bucket)
    train_data, validation_data = train_test_split(data, test_size=0.2)


    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        tf.train.write_graph(sess.graph_def, './src/tl_detector/light_classification/traffic_light_classifier/model_v12/','model_v12.pb')
        print("Training...")
        for i in range(10):
            print("EPOCH {} ...".format(i))
            for X_batch, y_batch in generator(bucket, train_data,num_classes , resize=resize):
                sess.run(optimizer, feed_dict={x: X_batch, y: y_batch, drop_out:0.5})
            val_generator = generator(bucket, validation_data,num_classes, resize=resize)
            validation_accuracy = evaluate(validation_data, val_generator)

            print("Validation Accuracy = {:.3f}".format(validation_accuracy))
        saver.save(sess, "./src/tl_detector/light_classification/traffic_light_classifier/model_v12/model_v12.ckpt")
        print("Model saved")

if __name__ == "__main__":
    start()
