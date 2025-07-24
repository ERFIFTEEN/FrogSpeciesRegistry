import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from cryptography.fernet import Fernet
import os

class FrogSpeciesRegistryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Frog Species Registry")
        self.root.geometry("450x350")

        # Initialize encryption
        self.key_file = "key.key"
        self.cipher = self.load_or_generate_key()

        # Initialize SQLite database
        self.conn = sqlite3.connect("frog_registry.db")
        self.create_table()

        # GUI Elements
        tk.Label(root, text="Species Name:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.species_entry = tk.Entry(root)
        self.species_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Genus:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.genus_entry = tk.Entry(root)
        self.genus_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(root, text="Habitat:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.habitat_entry = tk.Entry(root)
        self.habitat_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(root, text="Conservation Status:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.status_combobox = ttk.Combobox(root, values=[
            "Least Concern", "Near Threatened", "Vulnerable", "Endangered", "Critically Endangered", "Extinct"
        ], state="readonly")
        self.status_combobox.grid(row=3, column=1, padx=10, pady=5)
        self.status_combobox.set("Least Concern")

        tk.Button(root, text="Save Record", command=self.save_record).grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(root, text="View Registry", command=self.view_registry).grid(row=5, column=0, columnspan=2, pady=10)

    def load_or_generate_key(self):
        # Load or generate encryption key
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as key_file:
                key = key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as key_file:
                key_file.write(key)
        return Fernet(key)

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_name TEXT NOT NULL,
                genus TEXT NOT NULL,
                habitat TEXT NOT NULL,
                conservation_status TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def save_record(self):
        species_name = self.species_entry.get().strip()
        genus = self.genus_entry.get().strip()
        habitat = self.habitat_entry.get().strip()
        conservation_status = self.status_combobox.get()

        # Basic validation
        if not species_name or not genus or not habitat or not conservation_status:
            messagebox.showerror("Error", "All fields are required!")
            return

        # Encrypt species name
        try:
            encrypted_species = self.cipher.encrypt(species_name.encode()).decode()
        except Exception as e:
            messagebox.showerror("Error", f"Encryption failed: {str(e)}")
            return

        # Save to database
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO frogs (species_name, genus, habitat, conservation_status) VALUES (?, ?, ?, ?)",
                       (encrypted_species, genus, habitat, conservation_status))
        self.conn.commit()

        messagebox.showinfo("Success", "Frog species record saved successfully!")
        self.species_entry.delete(0, tk.END)
        self.genus_entry.delete(0, tk.END)
        self.habitat_entry.delete(0, tk.END)
        self.status_combobox.set("Least Concern")

    def view_registry(self):
        # Create a new window for the registry
        registry_window = tk.Toplevel(self.root)
        registry_window.title("Frog Species Registry")
        registry_window.geometry("650x400")

        # Create Treeview to display data
        tree = ttk.Treeview(registry_window, columns=("ID", "Species", "Genus", "Habitat", "Conservation Status"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Species", text="Species Name")
        tree.heading("Genus", text="Genus")
        tree.heading("Habitat", text="Habitat")
        tree.heading("Conservation Status", text="Conservation Status")
        tree.column("ID", width=50)
        tree.column("Species", width=150)
        tree.column("Genus", width=100)
        tree.column("Habitat", width=150)
        tree.column("Conservation Status", width=150)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Fetch and display data
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM frogs")
        for row in cursor.fetchall():
            # Decrypt species name
            try:
                decrypted_species = self.cipher.decrypt(row[1].encode()).decode()
            except Exception:
                decrypted_species = "Decryption Error"
            tree.insert("", tk.END, values=(row[0], decrypted_species, row[2], row[3], row[4]))

    def __del__(self):
        # Close database connection when the app closes
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = FrogSpeciesRegistryApp(root)
    root.mainloop()
