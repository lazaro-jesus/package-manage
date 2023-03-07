import subprocess
import json

from pathlib import Path


BASE_DIR: Path = Path(__file__).resolve().parent

SETTINGS = BASE_DIR / 'settings.json'

WARNING_INSTALL = '!Recomendable activar un entorno virtual antes de esta operacion!\n< Ctrl + C > para salir\n\n'

WARNING_UNINSTALL = '!Se desinstalará el paquete {0}! Precione (S/n) para proceder: '

ERROR = '\n(Precione Enter para salir)'

OPTIONS = '''<<<< Gestor de paquetes offline >>>>

< 1 > Descargar paquete(s)
< 2 > Instalar paquete(s)
< 3 > Listar paquetes descargados
< 4 > Cambiar directorio de descarga
< 5 > Desinstalar paquete(s)
< 0 > Salir

Seleccione una opcion: '''


def __check_default_repository() -> str:
    repository: Path = BASE_DIR / 'repository'
    repository.mkdir(exist_ok=True)
    
    return str(repository)


def __write_directory() -> None:
    repository = __check_default_repository()
        
    with open(SETTINGS, 'w', encoding='utf-8') as file:
        json.dump({'DIRECTORY': repository}, file, indent=4)
        
    return str(repository)


def clear_console() -> None:
    subprocess.call('cls', shell=True)


def end_program():
    clear_console()
    print('Gracias. Vuelva pronto...')
    exit()
    

def check_repository() -> str:
    if not SETTINGS.exists():
        return __write_directory()
    
    with open(SETTINGS, 'r', encoding='utf-8') as file:
        try:
            config: dict = json.load(file)
            default_repository: str = __check_default_repository()
            return config.get("DIRECTORY", default_repository)
        
        except json.decoder.JSONDecodeError:
           return __write_directory()


def change_repository(path: str) -> bool:
    new_path: Path = Path(path).resolve()
    if not new_path.exists():
        return False 
    
    with open(SETTINGS, 'r', encoding='utf-8') as file:
        config: dict = json.load(file)
        
    config["DIRECTORY"] = path
    
    with open(SETTINGS, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4)
        
    return True


def header(func):
    def wrapper(*args, **kwargs):
        clear_console()
        print('< 0 > Regresar\n')
        
        return func(*args, **kwargs)

    return wrapper


def header_freeze(func):
    def wrapper(*args, **kwargs):
        clear_console()
        head_menu = '< 0 > Regresar\n'
        freeze = subprocess.check_output('pip freeze').decode()

        if freeze != '':
            head_menu += f'\nPaquetes instalados en el entorno virtual actual:\n{freeze}\n'
        
        print(head_menu)
        
        return func(*args, **kwargs)

    return wrapper


@header
def download(repository: str, package: str|None = None): 
    package = input('Intruduzca su paquete a descargar: ')
    
    if package == '0': return
    
    output = subprocess.run(['pip', 'download', '-d', repository, package])

    if output.returncode == 1: input(ERROR)


@header_freeze
def install(repository: str, package: str|None = None):
    if package is None:
        package = input(WARNING_INSTALL + 'Intruduzca su paquete a instalar: ')
    else:
        clear_console()
        
    if package == '0': return

    output = subprocess.run(
        ['pip', 'install', '--no-index', f'--find-links={repository}', package], stderr = subprocess.PIPE)

    if output.returncode != 0 and 'Could not find a version' in output.stderr.decode():
        confirm = input(f'No se encontró el paquete {package}. Desea descargarlo? (S/n): ')
        if confirm.lower() != 's':
            return
        output = subprocess.run(['pip', 'download', '-d', repository, package])

    if output.returncode == 1: input(ERROR)


@header_freeze
def uninstall(repository: str, package: str|None = None):
    if package is None:
        package = input('Intruduzca su paquete a desinstalar: ')
    else:
        clear_console()
        
    if package == '0': return 

    confirm = input(WARNING_UNINSTALL.format(package))
    
    if confirm.lower() == 's':
        output = subprocess.run(['pip', 'uninstall', '--yes', package])

        if output.returncode == 1: input(ERROR)

    else:
        uninstall()


@header_freeze
def package_list(repository: str):
    pack_list = [pack.name for pack in Path(repository).absolute().iterdir()]
    
    for i, package in enumerate(pack_list):
        package = package.split('-', 2)
        package = '-'.join(package[:2])
        print(f'({i + 1:2d}) {package}')
        
    _input = input('\n' + WARNING_INSTALL + 'Puede instalar paquete introciendo su índice\n> ')
            
    if _input.isnumeric() and int(_input) in range(1, len(pack_list)):
        install(repository, pack_list[int(_input) - 1])
    

@header
def change_directory(repository: str):
    directory = input('Intruduzca la nueva ruta de descarga: ')
    
    if directory == '0': return 
    
    confirm = change_repository(directory)
    
    if confirm: return
    
    print('La ruta no es válida')
    input(ERROR)


def main():
    _input: str = ''
    repository: str = check_repository()
       
    COMMANDS = {
        '1': download,
        '2': install,
        '3': package_list,
        '4': change_directory,
        '5': uninstall
    }

    while _input != '0':
        clear_console()
        _input = input(f'Ruta: {repository}\n\n{OPTIONS}')

        if _input in COMMANDS.keys():
            COMMANDS[_input](repository)
        
    else:
        end_program()


if __name__ == '__main__':
    try:
        main()    
    except KeyboardInterrupt:
        end_program()