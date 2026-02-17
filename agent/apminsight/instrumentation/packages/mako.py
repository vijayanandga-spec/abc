from apminsight import constants

module_info = {
    "mako.template": [
        {constants.class_str: "Template", constants.method_str: "render", constants.component_str: constants.mako_comp},
        {constants.method_str: "_compile_text", constants.component_str: constants.mako_comp},
        {constants.method_str: "_compile_module_file", constants.component_str: constants.mako_comp},
    ]
}
