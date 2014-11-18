import json

import pymei
import gamera.core
import gamera.gamera_xml
import gamera.classify
import gamera.knn
from gamera.core import load_image

from rodan.jobs.gamera.custom.pitch_finding.AomrObject import AomrObject
from rodan.jobs.gamera.custom.pitch_finding.AomrMeiOutput import AomrMeiOutput
from rodan.jobs.gamera.custom.pitch_finding.AomrExceptions import AomrUnableToFindStavesError
from rodan.jobs.base import RodanAutomaticTask


class PitchFindingTask(RodanAutomaticTask):
    name = 'gamera.custom.pitch_finding.pitch_finding'
    author = "Deepanjan Roy"
    description = "Classifies the neumes detected in the page using the classifier interface."
    enabled = True
    category = "Pitch Finding"
    settings = [{'default': 2, 'has_default': True, 'rng': [1, 1048576], 'name': 'discard_size', 'type': 'int'}]

    input_port_types = [{
        'name': 'Segmented Image',
        'resource_types': ['image/onebit+png'],
        'minimum': 1,
        'maximum': 1
    }, {
        'name': 'Classifier Result',
        'resource_types': ['application/gamera+xml'],
        'minimum': 1,
        'maximum': 1
    }]
    output_port_types = [{
        'name': 'output',
        'resource_types': ['application/mei+xml'],
        'minimum': 1,
        'maximum': 1
    }]

    def run_my_task(self, inputs, rodan_job_settings, outputs):
        settings = argconvert.convert_to_gamera_settings(rodan_job_settings)
        gamera_xml_path = inputs['Classifier Result'][0]['resource_path']
        segmented_image_path = inputs['Segmented Image'][0]['resource_path']

        segmented_image = load_image(segmented_image_path)
        rank_image = segmented_image.rank(9, 9, 0)
        try:
            aomr_obj = AomrObject(rank_image,
                                  discard_size=settings['discard_size'],
                                  lines_per_staff=4,
                                  staff_finder=0,
                                  staff_removal=0,
                                  binarization=0)
            glyphs = gamera.gamera_xml.glyphs_from_xml(gamera_xml_path)
            recognized_glyphs = aomr_obj.run(glyphs)
            data = json.loads(recognized_glyphs)
            mei_file = AomrMeiOutput(data, segmented_image_path, '')
        except AomrUnableToFindStavesError as e:
            #if something goes wrong, this will create an empty mei file (instead of crashing)
            print e
            mei_file = AomrMeiOutput({}, segmented_image_path, '')

        pymei.write(mei_file.md, outputs['output'][0]['resource_path'])
