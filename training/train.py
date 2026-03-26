from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, TrainingArguments, Trainer
from data_preprocessing import preprocess
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, TaskType
import numpy as np
import evaluate
import sys

# Set data mappings
id2label = {0:'work', 1:'personal', 2:'finance & bills', 3:'scheduling & travel', 4:'marketing', 5:'notifications', 6:'spam'}
label2id = {'work':0, 'personal':1, 'finance & bills':2, 'scheduling & travel':3, 'marketing':4, 'notifications':5, 'spam':6}

# Set the model
model_name = 'google-bert/bert-base-uncased'

# Import the model and setup for our classification task
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=7, id2label=id2label, label2id=label2id)

# Freeze layers
for name,param in model.base_model.named_parameters():
    param.requires_grad=False

# Unfreeze base model pooling layers
for name, param in model.base_model.named_parameters():
    if "pooler" in name:
        param.requires_grad=True

# Configure LoRA
peft_config = LoraConfig(
    task_type = TaskType.SEQ_CLS,
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.01,
    target_modules=['query', 'value']
)

# Apply LoRA to model
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

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

# Function that preprocesses and tokenizes the dataset
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

# Set up evaluation metrics
accuracy = evaluate.load('accuracy')
f1_score = evaluate.load('f1')

def compute_metrics(eval_pred):
    # Get predictions
    predictions, labels = eval_pred
    
    # Apply softmax to get probabilities
    probabilities = np.exp(predictions) / np.exp(predictions).sum(-1, keepdims=True)
    
    # Predict most probable class
    predicted_class = np.argmax(probabilities, axis=1)

    # Calculate accuracy
    acc = np.round(accuracy.compute(predictions=predicted_class, references=labels))
    
    # Calculate f1
    f1 = f1_score.compute(predictions=predicted_class, references=labels, average='macro')
    
    return {"Accuracy":acc, "F1": f1}

# Set up training arguments
lr = 5e-5
batch_size = 8
num_epochs = 10

training_args = TrainingArguments(output_dir='/app/models',
                               num_train_epochs=num_epochs,
                               learning_rate=lr,
                               per_device_train_batch_size=batch_size,
                               per_device_eval_batch_size=batch_size,
                               warmup_steps=0.4,
                               weight_decay=0.001,
                               logging_strategy='epoch',
                               eval_strategy='epoch',
                               save_strategy='epoch',
                               load_best_model_at_end=True
                               )

# Set up trainer
trainer = Trainer(model=model,
                  args=training_args,
                  data_collator=data_collator,
                  train_dataset=dataset['train'],
                  eval_dataset=dataset['validation'],
                  processing_class=tokenizer,
                  compute_metrics=compute_metrics
                  )

# Train the model
trainer.train()