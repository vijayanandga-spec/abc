from apminsight import constants

module_info = {
    "genshi.template": [
        {
            constants.class_str: "Template",
            constants.method_str: "generate",
            constants.component_str: constants.genshi_comp,
        }
    ],
    "genshi": [
        {constants.class_str: "Stream", constants.method_str: "render", constants.component_str: constants.genshi_comp}
    ],
}
