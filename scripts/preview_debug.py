import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
from core.database import get_latest_analysis
from core.insat_reader import load_insat_scene

print('DEMO_DATA_FILE ->', Config.DEMO_DATA_FILE)
latest = get_latest_analysis(include_threats=False)
print('Latest:', latest and latest.get('id'))
path = latest.get('source_path') if latest else Config.DEMO_DATA_FILE
print('Using path:', path)
try:
    scene = load_insat_scene(path)
    print('Loaded scene keys:', list(scene.keys()))
    print('thermal shape:', scene['thermal'].shape)
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR:', e)
