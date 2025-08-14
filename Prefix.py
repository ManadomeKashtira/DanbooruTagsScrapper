def add_prefix_to_file(input_file, output_file, prefix):
    try:
        # Read lines from the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Add prefix to each name
        updated_lines = [f"{prefix}{line.strip()}\n" for line in lines]
        
        # Write updated lines to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print(f"Prefix file saved to: {output_file}")
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

if __name__ == "__main__":
    # --- Customize these values ---
    input_file = "YourTextFile.txt"       # your input file with names
    output_file = "art1.txt"
    prefix = "TEST"                # the text you want to add in front
    # ------------------------------

    add_prefix_to_file(input_file, output_file, prefix)
