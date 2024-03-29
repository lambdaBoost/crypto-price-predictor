
# coding: utf-8
#now tuning only on learning rate
#adam with constant low learning rate and cell option 3 provides best result so far rate=0.000043
#proximaladagrad optimiser looks promsing
#extremely sensitive to learning rate


# # TODO:
#need a custom loss function to maximise profit...or do we?


# In[1]:


import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import sklearn
from random import shuffle
from random import randint
import random
from scipy.stats.stats import pearsonr
from sklearn import preprocessing



# ### The Data

# In[2]:
raw_data = pd.read_csv("C:\\Users\\Alex\\Documents\\GitHub\\crypto-predictor\\crypto-price-predictor\\crypto-markets.csv")

btc_data = raw_data[raw_data['symbol']=="BTC"]

#this may come in handy later
btc_data=btc_data.ix[:,['date','open','close']]
btc_data['change_percent']=100*(btc_data['close']-btc_data['open'])/btc_data['open']

#for now we'll just take the daily change and predict the next day's change
close_price_data=np.array(btc_data['change_percent'])###


# In[5]:
tf.reset_default_graph()

# Num of steps in batch (also used for prediction steps into the future)
num_time_steps = 28
scale_data=True

#split into batches of 'num_time_Steps +1' days (the last element will be the y_true for the relevant batch)
data_batches=list() #list of 2 week batches to be used as train/test set
data_batches_shifted=list() #shift by 1 day to get y values
i=0
while (i < len(close_price_data)-num_time_steps-1):
    data_batches.append((close_price_data[i:(i+num_time_steps)]))
    i=i+1

data_batches=np.asarray(data_batches)


i=1
while (i < len(close_price_data)-num_time_steps):
    data_batches_shifted.append((close_price_data[i+num_time_steps]))###
    i=i+1

data_batches_shifted=np.asarray(data_batches_shifted)



#keep unscaled sets for now (may be useful later)
data_batches_unscaled=data_batches


#scale each batch relative to max value
def scale_batch(batch,shifted_batch):
    all_standardised=sklearn.preprocessing.scale(np.append(batch,shifted_batch))
    scaled_batch=all_standardised[0:num_time_steps]
    return scaled_batch

#as above but scales the true values
def scale_true(shifted_batch,batch):
    all_standardised=sklearn.preprocessing.scale(np.append(batch,shifted_batch))
    scaled_batch=all_standardised[num_time_steps]
    return scaled_batch
    
if(scale_data==True):
    
    data_batches_normalised=np.empty(shape=np.shape(data_batches))
    for i in range(0,len(data_batches)):
        data_batches_normalised[i]=scale_batch(data_batches[i],data_batches_shifted[i])
    
    data_batches_shifted_normalised=np.empty(shape=np.shape(data_batches_shifted))
    for i in range(0,len(data_batches_shifted)):
        data_batches_shifted_normalised[i]=scale_true(data_batches_shifted[i],data_batches[i])

else:
    data_batches_normalised=data_batches
    data_batches_shifted_normalised=data_batches_shifted


# In[6]:
#MAKE TRAIN AND TEST SET 
train_indices=random.sample(range(0,len(data_batches_normalised)),int(0.8*len(data_batches_normalised)))

x_train=data_batches_normalised[train_indices]
x_test=np.delete(data_batches_normalised,train_indices,0)
y_train=data_batches_shifted_normalised[train_indices]
y_test=np.delete(data_batches_shifted_normalised,train_indices,0)




# In[8]:
#pick a random training instance and plot it

#train_inst = x_train[np.random.randint(len(X_train))]


#plt.plot(list(range(0,num_time_steps+1)),train_inst)
#plt.title("random training instance")
#plt.tight_layout()


# # Creating the Model

# In[11]:


#tf.reset_default_graph()


# ### Constants

# In[12]:


# Just one feature, the time series
num_inputs = 1
# 100 neuron layer, play with this
num_neurons = 100
# Just one output, predicted time series
num_outputs = 1

# how many iterations to go through (training steps), you can play with this
num_train_iterations = len(x_train)
# Size of the batch of data
batch_size = 1


# ### Placeholders

# In[13]:


X = tf.placeholder(tf.float32, [None,num_time_steps,num_inputs])
y = tf.placeholder(tf.float32, [None,1,num_outputs])


#hyperparameter tuning
#%%
#tuning parameters
#start learning rate
k=0.000043


lr_list=list()
pearson_list=list() # select model with highest value of this
n_neuron_list=list()
n_layers_list=list()


    

        

#%%


# ____
# ____
# ### RNN Cell Layer
# 
# Play around with the various cells in this section, compare how they perform against each other.

# In[14]:


#cell = tf.contrib.rnn.OutputProjectionWrapper(
#    tf.contrib.rnn.BasicRNNCell(num_units=num_neurons, activation=tf.nn.relu),
#    output_size=num_outputs)


# In[15]:


#cell = tf.contrib.rnn.OutputProjectionWrapper(
#    tf.contrib.rnn.BasicLSTMCell(num_units=num_neurons, activation=tf.nn.relu),
#    output_size=num_outputs)#num_outputs


# In[16]:


n_neurons = 200#randint(min_neurons,max_neurons)
        #n_neuron_list.append(n_neurons)
n_layers = 10#randint(min_layers,max_layers)
        #n_layers_list.append(n_layers)
cell = tf.contrib.rnn.OutputProjectionWrapper(tf.contrib.rnn.MultiRNNCell([tf.contrib.rnn.BasicRNNCell(num_units=n_neurons) for layer in range(n_layers)]),output_size=num_outputs)###changed reuse to t


# In[17]:


#cell = tf.contrib.rnn.BasicLSTMCell(num_units=num_neurons, activation=tf.nn.relu)


# In[18]:


#n_neurons = 200
#n_layers = 10

#cell = tf.contrib.rnn.OutputProjectionWrapper(tf.contrib.rnn.MultiRNNCell([tf.contrib.rnn.BasicLSTMCell(num_units=n_neurons)
#          for layer in range(n_layers)]),output_size=num_outputs)


# _____
# _____

# ### Dynamic RNN Cell

# In[19]:


outputs, states = tf.nn.dynamic_rnn(cell, X, dtype=tf.float32)


# ### Loss Function and Optimizer

# In[20]:



#learning_rate = random.uniform(min_k,max_lr)
global_step = tf.Variable(0, trainable=False,dtype=tf.int64)
loss = tf.reduce_mean(tf.square(outputs[0][num_time_steps-1][0] - y[0])) # RMSE - minimised for the last day of the series (ie the unknown one)

#choose one or the other of the following 2 blocks (constant or decaying learning rate)
optimizer = tf.train.AdamOptimizer(learning_rate=k)
learning_step = optimizer.minimize(loss)

#global_step = tf.Variable(0, trainable=False)
#decay_steps=1 #decay the rate every step
#learning_rate = tf.train.inverse_time_decay(learning_rate, global_step,decay_steps, 0.5)
# Passing global_step to minimize() will increment it at each step.
#learning_step = (tf.train.ProximalAdagradOptimizer(learning_rate).minimize(loss, global_step=global_step))


# #### Init Variables

# In[21]:


init = tf.global_variables_initializer()


# ## Session

# In[24]:


# ONLY FOR GPU USERS:
# https://stackoverflow.com/questions/34199233/how-to-prevent-tensorflow-from-allocating-the-totality-of-a-gpu-memory
#gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.75)


# In[25]:


saver = tf.train.Saver()

# In[26]:


with tf.Session() as sess:
    sess.run(init)
    
    loss_list=list()
    iteration_list=list()
    
    for iteration in range(num_train_iterations):
        
        X_batch = np.reshape(x_train[iteration],(batch_size,num_time_steps,num_inputs))
        y_batch = np.reshape(y_train[iteration],(batch_size,1,num_outputs))
        sess.run(learning_step, feed_dict={X: X_batch, y: y_batch})
        
        
        
        if iteration % 10 == 0:
            
            
            rmse = loss.eval(feed_dict={X: X_batch, y: y_batch})
               # print(iteration, "\tRMSE:", rmse)
            
            #accuracy on test set
            test_rmse=loss.eval(feed_dict={X: np.reshape(x_test,( np.shape(x_test)[0],np.shape(x_test)[1],1)),y:np.reshape(y_test,( np.shape(y_test)[0],1,1))})
               # print(iteration, "\tRMSE on test:", test_rmse)
            
            loss_list.append(test_rmse)
            iteration_list.append(iteration)
    # Save Model for Later
    saver.save(sess, "./rnn_time_series_model")





# ### Predicting a time series 

# In[27]:


with tf.Session() as sess:                          
    saver.restore(sess, "./rnn_time_series_model")   
    
    random_selection=randint(0,len(x_test))
    X_new = np.reshape(x_test[random_selection],(1,num_time_steps,num_inputs))
    y_true = np.reshape(y_test[random_selection],(1,1,1))
    y_pred = sess.run(outputs, feed_dict={X: X_new})
    
    y_pred_list=sess.run(outputs,feed_dict={X:np.reshape(x_test,(len(x_test),np.shape(x_test)[1],1))})

# In[28]:
#plot example prediction
    plt.figure(0)
    plt.title("Testing Example")

# Test Instance
    plt.plot(list(range(0,num_time_steps)),X_new[0],label="Input")
    plt.plot(num_time_steps, y_true[0],'ro',label="Actual")

# Target to Predict
    plt.plot(list(range(1,num_time_steps+1)), y_pred[0],'bs', label="Predicted")


    plt.xlabel("Time")
    plt.legend()
    plt.tight_layout()

    axes = plt.gca()
    axes.set_ylim([min(X_new[0])[0],max(X_new[0])[0]])




predicted_list=list()
#scatter plot of all predicted vs actuals
for i in range(0,len(y_pred_list)):
    predicted_list.append(y_pred_list[i][num_time_steps-1][0]) #take the last one (ie the unknown day)
    
    plt.figure(1)
    plt.title("predicted vs actuals")
    plt.scatter(predicted_list,y_test)
    plt.xlabel("predicted")
    plt.ylabel("actual")

#plot loss
    plt.figure(2)
    plt.title("loss function")
    plt.plot(iteration_list,loss_list)

#pearson correlation
#pearson_list.append(pearsonr(predicted_list,y_test))
#lr_list.append(learning_rate)
        #tf.reset_default_graph()
        
        #print(k)
        #k=k+1