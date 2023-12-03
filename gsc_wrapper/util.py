import pathlib


class Util:
    @staticmethod
    def get_filename(destination: str, filename: str):
        unique_path = destination / filename

        if pathlib.Path(unique_path).is_file():
            filename = filename.replace(".pck", "{:03d}.pck")
            counter = 0
            while True:
                counter += 1
                if not pathlib.Path(filename.format(counter)).is_file():
                    break

        return unique_path
