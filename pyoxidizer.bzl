# This file defines how PyOxidizer application building and packaging is
# performed. See PyOxidizer's documentation at
# https://pyoxidizer.readthedocs.io/en/stable/ for details of this
# configuration file format.

def resource_callback(policy, resource):
    if type(resource) in ("File"):
        if "pywin" in resource.path or "pypiwin" in resource.path:
            resource.add_location = "filesystem-relative:lib"
            resource.add_include = True

    if type(resource) in ("PythonExtensionModule"):
        if resource.name in ["_ssl", "win32.win32file", "win32.win32pipe"]:
            resource.add_location = "filesystem-relative:lib"
            resource.add_include = True
    elif type(resource) in ("PythonModuleSource", "PythonPackageResource", "PythonPackageDistributionResource"):
        if resource.name in ["pywin32_bootstrap", "pythoncom", "pypiwin32", "pywin32", "pythonwin", "win32", "win32com", "win32comext"]:
            resource.add_location = "filesystem-relative:lib"
            resource.add_include = True

def resource_callback1(policy, resource):
    if type(resource) in ("File"):
        if "pywin" in resource.path or "pypiwin" in resource.path:
            resource.add_location = "in-memory"
            resource.add_include = True

    if type(resource) in ("PythonExtensionModule"):
        if resource.name in ["_ssl", "win32.win32file", "win32.win32pipe"]:
            resource.add_location = "in-memory"
            resource.add_include = True
    elif type(resource) in ("PythonModuleSource", "PythonPackageResource", "PythonPackageDistributionResource"):
        if resource.name in ["pywin32_bootstrap", "pythoncom", "pypiwin32", "pywin32", "pythonwin", "win32", "win32com", "win32comext"]:
            resource.add_location = "in-memory"
            resource.add_include = True


def make_exe():
    # Obtain the default PythonDistribution for our build target. We link
    # this distribution into our produced executable and extract the Python
    # standard library from it.
    dist = default_python_distribution(flavor="standalone")

    # This function creates a `PythonPackagingPolicy` instance, which
    # influences how executables are built and how resources are added to
    # the executable. You can customize the default behavior by assigning
    # to attributes and calling functions.
    policy = dist.make_python_packaging_policy()


    # Control support for loading Python extensions and other shared libraries
    # from memory. This is only supported on Windows and is ignored on other
    # platforms.
    policy.allow_in_memory_shared_library_loading = True

    # Control whether to generate Python bytecode at various optimization
    # levels. The default optimization level used by Python is 0.
    # policy.bytecode_optimize_level_zero = True
    policy.bytecode_optimize_level_one = True
    # policy.bytecode_optimize_level_two = True

    policy.extension_module_filter = "all"

    # Controls the `add_include` attribute of `File` resources.
    policy.include_file_resources = True
    # policy.set_resource_handling_mode("files")

    # Controls the `add_include` attribute of `PythonModuleSource` not in
    # the standard library.
    # policy.include_non_distribution_sources = False

    policy.include_test = False
    policy.resources_location = "in-memory"
    policy.resources_location_fallback = "in-memory"
    policy.allow_files = True
    policy.file_scanner_emit_files = True
    policy.register_resource_callback(resource_callback1)
    python_config = dist.make_python_interpreter_config()
    python_config.module_search_paths = ["$ORIGIN", "$ORIGIN/lib"]

    python_config.run_command = "from getdeck.__main__ import main; main()"

    exe = dist.to_python_executable(
        name="deck",
        packaging_policy=policy,
        config=python_config,
    )

    exe.add_python_resources(exe.read_package_root(CWD, ["getdeck"]))
    exe.add_python_resources(exe.setup_py_install("./build/pywin32/", extra_global_arguments=["--skip-verstamp"]))
    exe.add_python_resources(exe.pip_install(["--no-deps", "docker"]))
    exe.add_python_resources(exe.pip_install(["--no-binary", ":all:", "PyYAML", "pydantic", "kubernetes"]))
    
    exe.add_python_resources(exe.pip_install(["semantic-version==2.9.0", "GitPython==3.1.27"]))

    
    exe.windows_runtime_dlls_mode = "always"

    return exe

def make_embedded_resources(exe):
    return exe.to_embedded_resources()

def make_install(exe):
    # Create an object that represents our installed application file layout.
    files = FileManifest()

    # Add the generated executable to our install layout in the root directory.
    files.add_python_resource(".", exe)

    return files

def make_msi(exe):
    # See the full docs for more. But this will convert your Python executable
    # into a `WiXMSIBuilder` Starlark type, which will be converted to a Windows
    # .msi installer when it is built.
    return exe.to_wix_msi_builder(
        # Simple identifier of your app.
        "myapp",
        # The name of your application.
        "My Application",
        # The version of your application.
        "1.0",
        # The author/manufacturer of your application.
        "Alice Jones"
    )


# Dynamically enable automatic code signing.
def register_code_signers():
    # You will need to run with `pyoxidizer build --var ENABLE_CODE_SIGNING 1` for
    # this if block to be evaluated.
    if not VARS.get("ENABLE_CODE_SIGNING"):
        return

    # Use a code signing certificate in a .pfx/.p12 file, prompting the
    # user for its path and password to open.
    # pfx_path = prompt_input("path to code signing certificate file")
    # pfx_password = prompt_password(
    #     "password for code signing certificate file",
    #     confirm = True
    # )
    # signer = code_signer_from_pfx_file(pfx_path, pfx_password)

    # Use a code signing certificate in the Windows certificate store, specified
    # by its SHA-1 thumbprint. (This allows you to use YubiKeys and other
    # hardware tokens if they speak to the Windows certificate APIs.)
    # sha1_thumbprint = prompt_input(
    #     "SHA-1 thumbprint of code signing certificate in Windows store"
    # )
    # signer = code_signer_from_windows_store_sha1_thumbprint(sha1_thumbprint)

    # Choose a code signing certificate automatically from the Windows
    # certificate store.
    # signer = code_signer_from_windows_store_auto()

    # Activate your signer so it gets called automatically.
    # signer.activate()


# Call our function to set up automatic code signers.
register_code_signers()

# Tell PyOxidizer about the build targets defined above.
register_target("exe", make_exe)
register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
register_target("install", make_install, depends=["exe"], default=True)
register_target("msi_installer", make_msi, depends=["exe"])

# Resolve whatever targets the invoker of this configuration file is requesting
# be resolved.
resolve_targets()
