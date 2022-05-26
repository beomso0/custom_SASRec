# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from collections import defaultdict
import pickle 
import os
from .model import SASREC

class SASRecDataSet:
    """
    A class for creating SASRec specific dataset used during
    train, validation and testing.

    Attributes:
        usernum: integer, total number of users
        itemnum: integer, total number of items
        User: dict, all the users (keys) with items as values
        Items: set of all the items
        user_train: dict, subset of User that are used for training
        user_valid: dict, subset of User that are used for validation
        user_test: dict, subset of User that are used for testing
        col_sep: column separator in the data file
        filename: data filename
    """

    def __init__(self, **kwargs):
        self.usernum = 0
        self.itemnum = 0
        self.User = defaultdict(list)
        self.Items = set()
        self.user_train = {}
        self.user_valid = {}
        self.user_test = {}
        self.col_sep = kwargs.get("col_sep", " ")
        self.filename = kwargs.get("filename", None)

        if self.filename:
            with open(self.filename, "r") as fr:
                sample = fr.readline()
            ncols = sample.strip().split(self.col_sep)
            if ncols == 3:
                self.with_time = True
            else:
                self.with_time = False

    def split(self, **kwargs):
        self.filename = kwargs.get("filename", self.filename)
        if not self.filename:
            raise ValueError("Filename is required")

        if self.with_time:
            self.data_partition_with_time()
        else:
            self.data_partition()

    def data_partition(self):
        # assume user/item index starting from 1
        f = open(self.filename, "r")
        for line in f:
            u, i = line.rstrip().split(self.col_sep)
            u = int(u)
            i = int(i)
            self.usernum = max(u, self.usernum)
            self.itemnum = max(i, self.itemnum)
            self.User[u].append(i)

        for user in self.User:
            nfeedback = len(self.User[user])
            if nfeedback < 3:
                self.user_train[user] = self.User[user]
                self.user_valid[user] = []
                self.user_test[user] = []
            else:
                self.user_train[user] = self.User[user][:-2]
                self.user_valid[user] = []
                self.user_valid[user].append(self.User[user][-2])
                self.user_test[user] = []
                self.user_test[user].append(self.User[user][-1])

    def data_partition_with_time(self):
        # assume user/item index starting from 1
        f = open(self.filename, "r")
        for line in f:
            u, i, t = line.rstrip().split(self.col_sep)
            u = int(u)
            i = int(i)
            t = float(t)
            self.usernum = max(u, self.usernum)
            self.itemnum = max(i, self.itemnum)
            self.User[u].append((i, t))
            self.Items.add(i)

        for user in self.User.keys():
            # sort by time
            items = sorted(self.User[user], key=lambda x: x[1])
            # keep only the items
            items = [x[0] for x in items]
            self.User[user] = items
            nfeedback = len(self.User[user])
            if nfeedback < 3:
                self.user_train[user] = self.User[user]
                self.user_valid[user] = []
                self.user_test[user] = []
            else:
                self.user_train[user] = self.User[user][:-2]
                self.user_valid[user] = []
                self.user_valid[user].append(self.User[user][-2])
                self.user_test[user] = []
                self.user_test[user].append(self.User[user][-1])


def save_sasrec_model(model,path, exp_name='sas_experiment',**kwargs):
  
  # score suffix
  save_info = kwargs.get("save_info")
  score = save_info['score']
  epoch = save_info['epoch']
  
  # make dir
  if not os.path.exists(path+exp_name):
    os.mkdir(path+exp_name)

  model.save_weights(path+exp_name+'/'+exp_name+'_weights') # save trained weights
  arg_list = ['item_num','seq_max_len','num_blocks','embedding_dim','attention_dim','attention_num_heads','dropout_rate','conv_dims','l2_reg','num_neg_test']
  dict_to_save = {a: model.__dict__[a] for a in arg_list}
  with open(path+exp_name+'/'+exp_name+'_model_args','wb') as f:
    pickle.dump(dict_to_save, f)
  
  if not os.path.isfile(path+exp_name+'/'+exp_name+'_train_log.txt'): 
    with open(path+exp_name+'/'+exp_name+'_train_log.txt','w') as f:
      f.writelines(f'Model args: {dict_to_save}\n')
      f.writelines(f'[epoch {epoch}] Best HR@10 score: {score}\n')
  else:
    with open(path+exp_name+'/'+exp_name+'_train_log.txt','a') as f:
      f.writelines(f'[epoch {epoch}] Best HR@10 score: {score}\n')


def load_sasrec_model(path, exp_name='sas_experiment'):
  with open(path+exp_name+'/'+exp_name+'_model_args','rb') as f:
    arg_dict = pickle.load(f)
  model = SASREC(item_num=arg_dict['item_num'],
                   seq_max_len=arg_dict['seq_max_len'],
                   num_blocks=arg_dict['num_blocks'],
                   embedding_dim=arg_dict['embedding_dim'],
                   attention_dim=arg_dict['attention_dim'],
                   attention_num_heads=arg_dict['attention_num_heads'],
                   dropout_rate=arg_dict['dropout_rate'],
                   conv_dims = arg_dict['conv_dims'],
                   l2_reg=arg_dict['l2_reg'],
                   num_neg_test=arg_dict['num_neg_test'],
    )
  model.load_weights(path+exp_name+'/'+exp_name+'_weights')
  return model