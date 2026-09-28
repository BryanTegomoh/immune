"""Restore the newest completed hosted artifact without logging its contents."""
import io
import json
import os
import subprocess
import zipfile
from pathlib import Path


def gh(path):
    return subprocess.check_output(['gh', 'api', path])


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    runs = json.loads(gh(f'repos/{repo}/actions/workflows/hosted.yml/runs?branch=main&status=completed&per_page=50'))['workflow_runs']
    for run in runs:
        artifacts = json.loads(gh(f"repos/{repo}/actions/runs/{run['id']}/artifacts"))['artifacts']
        artifact = next((a for a in artifacts if a['name'] == 'immune-hosted-state' and not a['expired']), None)
        if not artifact:
            continue
        raw = gh(f"repos/{repo}/actions/artifacts/{artifact['id']}/zip")
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            info = archive.getinfo('state.json')
            if info.file_size > 5_000_000:
                raise ValueError('Saved state exceeds the size limit.')
            value = json.loads(archive.read(info))
        Path('runs/state.json').write_text(json.dumps(value, indent=2))
        print('Restored the most recent saved hosted state.')
        return
    print('No unexpired hosted state exists. Using the recorded synthetic seed.')


if __name__ == '__main__':
    main()
