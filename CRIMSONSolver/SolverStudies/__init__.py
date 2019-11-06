import pkgutil

module_exclude_list = ['flowsolver.plotNetlistCircuits3D',
					   'flowsolver.plotNetlistOutput']

__all__ = []
for loader, module_name, is_pkg in  pkgutil.walk_packages(__path__):
	if module_name not in module_exclude_list:
	    __all__.append(module_name)
	    module = loader.find_module(module_name).load_module(module_name)
	    exec('%s = module' % module_name)