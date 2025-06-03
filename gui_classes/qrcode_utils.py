import qrcode
from PIL import Image

class QRCodeGenerator:
    @staticmethod
    def generate_qrcode(data: str, box_size: int = 10, border: int = 4) -> Image.Image:
        """
        Génère un QR code à partir d'une chaîne de caractères.
        :param data: Le texte à encoder dans le QR code.
        :param box_size: Taille d'un carré du QR code.
        :param border: Largeur de la bordure (en carrés).
        :return: Un objet PIL.Image du QR code.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img
