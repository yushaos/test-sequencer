import os

class PreviousSequences:
    def __init__(self, property_folder="sequencer property", file_name="previous sequences.txt"):
        self.property_folder = property_folder
        self.file_name = file_name
        self.file_path = os.path.join(self.property_folder, self.file_name)

    def get_previous_sequences(self):
        if not os.path.exists(self.file_path):
            return []
        
        with open(self.file_path, 'r') as f:
            return f.read().splitlines()

    def add_sequence(self, sequence_file):
        sequences = self.get_previous_sequences()
        
        # Check if the new sequence is already at the top
        if sequences and sequences[0] == sequence_file:
            return
        
        # Remove the sequence if it's already in the list
        sequences = [seq for seq in sequences if seq != sequence_file]
        
        # Add the new sequence to the top
        sequences.insert(0, sequence_file)
        
        # Keep only the last 10 sequences
        sequences = sequences[:10]
        
        # Ensure the directory exists
        if not os.path.exists(self.property_folder):
            os.makedirs(self.property_folder)
        
        # Write the updated list back to the file
        with open(self.file_path, 'w') as f:
            f.write('\n'.join(sequences))
