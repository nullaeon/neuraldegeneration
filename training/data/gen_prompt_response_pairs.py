import os
import json
import time
from pathlib import Path
import openai

client = openai.OpenAI()

MAX_BATCHES=50

def generate_batch(batch_size=20, temperature=1.0, max_tokens=800):
    pairs = []
    base_prompt = (
        "Give me a unique prompt and response pair in the following format:\n\n"
        "Prompt: <prompt>\nResponse: <response>"
    )

    for _ in range(batch_size):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate an original prompt and a thoughtful response."},
                    {"role": "user", "content": base_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            text = response.choices[0].message.content.strip()

            if "Prompt:" in text and "Response:" in text:
                prompt_part = text.split("Prompt:")[1].split("Response:")[0].strip()
                response_part = text.split("Response:")[1].strip()
                pairs.append({"prompt": prompt_part, "response": response_part})
            else:
                print("Malformed response:", text)
            time.sleep(0.3)

        except Exception as e:
            print(f"API error: {e}")
            time.sleep(5)

    return pairs

def save_batch(pairs, batch_num, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"generation_batch_{batch_num:02d}.jsonl"
    with open(filename, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")
    return filename

if __name__ == "__main__":
    output_dir = Path("./")
    for batch_num in range(MAX_BATCHES):
        print(f"Generating batch {batch_num + 1}/50...")
        pairs = generate_batch(batch_size=20, temperature=1.0, max_tokens=600)
        save_batch(pairs, batch_num, output_dir)
        time.sleep(1)

