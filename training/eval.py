import torch
from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

# Load model and tokenizer
model = GPT2LMHeadModel.from_pretrained("llm0")
tokenizer = PreTrainedTokenizerFast(tokenizer_file="llm0/tokenizer.json")
tokenizer.pad_token = "<pad>"
tokenizer.bos_token = "<s>"
tokenizer.eos_token = "</s>"
tokenizer.unk_token = "<unk>"

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Define prompt
prompt = "<s>"  # or something like: "The sun rose over the"
inputs = tokenizer(prompt, return_tensors="pt").to(device)

# Generate text
with torch.no_grad():
    outputs = model.generate(
        input_ids=inputs["input_ids"],
        max_new_tokens=100,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.9,
        eos_token_id=tokenizer.eos_token_id,
    )

# Decode and print
generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n=== Generated Output ===\n")
print(generated)
