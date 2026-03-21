from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding
from data_preprocessing import preprocess
from datasets import load_dataset
import sys

# Set data mappings
id2label = {0:'work', 1:'personal', 2:'finance & bills', 3:'scheduling & travel', 4:'marketing', 5:'notifications', 6:'spam'}
label2id = {'work':0, 'personal':1, 'finance & bills':2, 'scheduling & travel':3, 'marketing':4, 'notifications':5, 'spam':6}

# # Set the model
model_name = 'google-bert/bert-base-uncased'

# # Import the model and setup for our classification task
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=7, id2label=id2label, label2id=label2id)

# Import tokenizer
tokenizer = AutoTokenizer.from_pretrained('google-bert/bert-base-uncased')

# Import training/testing data
data_path = '/app/data'
data_files = {'train': 'train_emails.csv', 'test':'test_emails.csv'} 
dataset = load_dataset(data_path, data_files=data_files)

############################################# REMOVE 'urgency' column for now. Will focus on setting up pipeline for category classification first #############################################
dataset['train'] = dataset['train'].remove_columns('urgency')
dataset['test'] = dataset['test'].remove_columns('urgency')
############################################# REMOVE 'urgency' column for now. Will focus on setting up pipeline for category classification first #############################################

# Create a validation set
split = dataset['train'].train_test_split(test_size=0.2)
dataset['train'], dataset['validation'] = split['train'], split['test']

print(dataset['validation']['body'][50])

# Function that tokenizes dataset
def tokenize_dataset(dataset):
    dataset['subject'] = preprocess(dataset['subject'], True)
    dataset['body'] = preprocess(dataset['body'], False)
    dataset['labels'] = label2id[dataset['category'].lower()]
    return tokenizer(dataset['subject'], dataset['body'], truncation=True)

# Tokenize the datasets
dataset['train'] = dataset['train'].map(tokenize_dataset, batched=False)
dataset['validation'] = dataset['validation'].map(tokenize_dataset, batched=False)
dataset['test'] = dataset['test'].map(tokenize_dataset, batched=False)

# Create a data collator
data_collator = DataCollatorWithPadding(tokenizer)

############################################################ NEXT STEPS: SET UP TRAINING ARUGMENTS AND TRAINER ######################################################################