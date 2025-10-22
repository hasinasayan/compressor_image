import os
import shutil
from pathlib import Path
from PIL import Image
import io
import logging
from datetime import datetime

class ImageCompressor:
    def __init__(self, folder_path):
        self.folder_path = Path(folder_path)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.avif'}
        self.quality_mapping = {
            '.jpg': 85,
            '.jpeg': 85,
            '.png': 95,
            '.webp': 85,
            '.avif': 80
        }
        self.stats = {
            'total_files': 0,
            'compressed': 0,
            'failed': 0,
            'original_size': 0,
            'compressed_size': 0
        }
        
    def get_extension(self, filename):
        """Extrait l'extension réelle du fichier"""
        name = str(filename).lower()
        if name.endswith(('.jpg.avif', '.jpg.webp')):
            return name[-9:]
        elif name.endswith(('.png.webp', '.png.avif')):
            return name[-8:]
        else:
            return Path(name).suffix

    def is_image(self, filename):
        """Vérifie si le fichier est une image supportée"""
        ext = self.get_extension(filename)
        return ext in self.supported_formats

    def compress_image(self, image_path):
        """Compresse une image avec optimisation"""
        temp_path = None
        try:
            original_size = os.path.getsize(image_path)

            # Ouvrir l'image
            img = Image.open(image_path)

            # Convertir RGBA en RGB si nécessaire (pour JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            ext = self.get_extension(image_path)
            quality = self.quality_mapping.get(ext, 85)

            # Créer un fichier temporaire
            temp_path = str(image_path) + '.tmp'

            if ext in ('.jpg', '.jpeg'):
                img.save(temp_path, 'JPEG', quality=quality, optimize=True)
            elif ext == '.png':
                img.save(temp_path, 'PNG', optimize=True)
            elif ext == '.webp':
                img.save(temp_path, 'WEBP', quality=quality, method=6)
            elif ext in ('.jpg.avif', '.png.avif'):
                img.save(temp_path, 'AVIF', quality=quality)
            else:
                return False

            # Vérifier que le fichier compressé est plus petit
            compressed_size = os.path.getsize(temp_path)

            if compressed_size < original_size:
                shutil.move(temp_path, image_path)
                self.stats['compressed_size'] += compressed_size
                return True
            else:
                os.remove(temp_path)
                self.stats['compressed_size'] += original_size
                return True

        except Exception as e:
            print(f"❌ Erreur avec {image_path}: {str(e)}")
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def process_folder(self):
        """Traite tous les fichiers images du dossier et sous-dossiers"""
        if not self.folder_path.exists():
            print(f"❌ Le dossier {self.folder_path} n'existe pas!")
            return False

        image_files = [f for f in self.folder_path.rglob('*')
                      if f.is_file() and self.is_image(f.name)]

        if not image_files:
            print("⚠️  Aucune image trouvée dans le dossier!")
            return False

        self.stats['total_files'] = len(image_files)
        print(f"\n🖼️  Traitement de {self.stats['total_files']} image(s)...\n")

        for i, image_path in enumerate(image_files, 1):
            original_size = os.path.getsize(image_path)
            self.stats['original_size'] += original_size

            print(f"[{i}/{self.stats['total_files']}] {image_path.name}...", end=" ")

            if self.compress_image(image_path):
                new_size = os.path.getsize(image_path)
                reduction = (1 - new_size / original_size) * 100
                print(f"✓ Réduit de {reduction:.1f}%")
                self.stats['compressed'] += 1
            else:
                print("✗")
                self.stats['failed'] += 1

        return True

    def print_summary(self):
        """Affiche un résumé des statistiques"""
        # Log de fin de traitement
        end_time = datetime.now()
        print(f"🕐 Fin du traitement: {end_time.strftime('%d/%m/%Y %H:%M:%S')}")

        print("\n" + "="*50)
        print("📊 RÉSUMÉ DE COMPRESSION")
        print("="*50)
        print(f"Total d'images: {self.stats['total_files']}")
        print(f"Compressées avec succès: {self.stats['compressed']}")
        print(f"Erreurs: {self.stats['failed']}")
        print(f"Taille originale: {self.format_size(self.stats['original_size'])}")
        print(f"Taille compressée: {self.format_size(self.stats['compressed_size'])}")

        if self.stats['original_size'] > 0:
            total_reduction = (1 - self.stats['compressed_size'] / self.stats['original_size']) * 100
            saved = self.stats['original_size'] - self.stats['compressed_size']
            print(f"Espace économisé: {self.format_size(saved)} ({total_reduction:.1f}%)")
        print("="*50 + "\n")

    @staticmethod
    def format_size(size_bytes):
        """Formate une taille en bytes en format lisible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"


if __name__ == "__main__":
    # CONFIGURATION
    folder_path = input("📁 Entrez le chemin du dossier contenant les images: ").strip()

    # Initialiser et lancer la compression
    compressor = ImageCompressor(folder_path)

    if compressor.process_folder():
        compressor.print_summary()
        print("✅ Compression terminée!")
    else:
        print("❌ La compression n'a pas pu être complétée.")