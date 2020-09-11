# from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# hiddenimports = collect_submodules('tensorflow_core')
# datas = collect_data_files('tensorflow_core', subdir=None, include_py_files=True)

from PyInstaller.utils.hooks import collect_all


def hook(hook_api):
    packages = [
        'tensorflow',
        # 'tensorboard',
        # 'tensorflow_estimator'
        'tensorflow_core',
        'astor'
    ]
    for package in packages:
        datas, binaries, hiddenimports = collect_all(package)
        hook_api.add_datas(datas)
        hook_api.add_binaries(binaries)
        hook_api.add_imports(*hiddenimports)