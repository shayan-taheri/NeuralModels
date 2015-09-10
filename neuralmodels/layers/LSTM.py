from headers import *

class LSTM(object):
	def __init__(self,activation_str='tanh',activation_gate='sigmoid',init='uniform',truncate_gradient=50,size=128,weights=None,seq_output=True,rng=None,skip_input=False,jump_up=False):
		self.settings = locals()
		del self.settings['self']
		self.activation = getattr(activations,activation_str)
		self.activation_gate = getattr(activations,activation_gate)
		self.truncate_gradient = truncate_gradient
		self.init = getattr(inits,init)
		self.size = size
		self.weights = weights
		self.seq_output = seq_output
		self.rng = rng
		self.skip_input = skip_input
		self.jump_up = jump_up

	def connect(self,layer_below,skip_layer=None):
		self.layer_below = layer_below
		self.skip_layer=skip_layer
		self.inputD = layer_below.size
		if self.skip_layer:
			self.inputD += skip_layer.size

		self.W_i = self.init((self.inputD,self.size),rng=self.rng)
		self.W_f = self.init((self.inputD,self.size),rng=self.rng)
		self.W_o = self.init((self.inputD,self.size),rng=self.rng)
		self.W_c = self.init((self.inputD,self.size),rng=self.rng)

		self.U_i = self.init((self.size,self.size),rng=self.rng)
		self.U_f = self.init((self.size,self.size),rng=self.rng)
		self.U_o = self.init((self.size,self.size),rng=self.rng)
		self.U_c = self.init((self.size,self.size),rng=self.rng)

		self.V_i = self.init((self.size,self.size),rng=self.rng)
		self.V_f = self.init((self.size,self.size),rng=self.rng)
		self.V_o = self.init((self.size,self.size),rng=self.rng)

		self.b_i = zero0s((1,self.size)) 
		self.b_f = zero0s((1,self.size))
		self.b_o = zero0s((1,self.size))
		self.b_c = zero0s((1,self.size))

		self.h0 = zero0s((1,self.size))
		self.c0 = zero0s((1,self.size))

		self.params = [self.W_i, self.W_f, self.W_o, self.W_c,
			self.U_i, self.U_f, self.U_o, self.U_c,
			self.b_i, self.b_f, self.b_o, self.b_c,
			self.V_i, self.V_f, self.V_o
			]

		if self.weights is not None:
			for param, weight in zip(self.params,self.weights):
				param.set_value(np.asarray(weight, dtype=theano.config.floatX))

		self.L2_sqr = (
				(self.W_i ** 2).sum() +
				(self.W_f ** 2).sum() +
				(self.W_o ** 2).sum() +
				(self.W_c ** 2).sum() +
				(self.U_i ** 2).sum() +
				(self.U_f ** 2).sum() +
				(self.U_o ** 2).sum() +
				(self.U_c ** 2).sum() 
			)

	def recurrence(self,x_t,h_tm1,c_tm1):
		i_t = self.activation_gate(T.dot(x_t, self.W_i) + T.dot(h_tm1, self.U_i) + T.dot(c_tm1, self.V_i) + T.extra_ops.repeat(self.b_i,x_t.shape[0],axis=0))
		f_t = self.activation_gate(T.dot(x_t, self.W_f) + T.dot(h_tm1, self.U_f) + T.dot(c_tm1, self.V_f) + T.extra_ops.repeat(self.b_f,x_t.shape[0],axis=0))
		c_tilda_t = self.activation(T.dot(x_t, self.W_c) + T.dot(h_tm1, self.U_c) + T.extra_ops.repeat(self.b_c,x_t.shape[0],axis=0))
		c_t = f_t * c_tm1 + i_t * c_tilda_t
		o_t = self.activation_gate(T.dot(x_t, self.W_o) + T.dot(h_tm1, self.U_o) + T.dot(c_t, self.V_o) + T.extra_ops.repeat(self.b_o,x_t.shape[0],axis=0))
		h_t = o_t * self.activation(c_t)

		return h_t,c_t

	def output(self):
		X = []
		if self.skip_layer:
			X = T.concatenate([self.layer_below.output(),self.skip_layer.output()],axis=2)
		else:
			X = self.layer_below.output() 
		[out, cells], ups = theano.scan(fn=self.recurrence,
					sequences=[X],
					outputs_info=[T.extra_ops.repeat(self.h0,X.shape[1],axis=0), T.extra_ops.repeat(self.c0,X.shape[1],axis=0)],
					n_steps=X.shape[0],
					truncate_gradient=self.truncate_gradient
				)
		if self.seq_output:
			return out
			# dim = T x N x self.size 
		else:
			return out[-1]
			# dim = N x self.size 

