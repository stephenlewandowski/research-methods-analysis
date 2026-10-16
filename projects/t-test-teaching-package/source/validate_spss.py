"""Run both teaching examples in an installed SPSS Python integration runtime.

Use IBM's statisticspython3 launcher, not the ordinary rendering environment.
Outputs are genuine OMS exports; the script does not emulate SPSS.
"""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


PACKAGE_DIR = Path(__file__).resolve().parents[1]


def quoted(path):
    return "'" + str(path).replace('\\', '/').replace("'", "''") + "'"


def local_name(node):
    return node.tag.rsplit('}', 1)[-1]


def numeric_categories(node):
    values = {}
    for category in node.iter():
        if local_name(category) != 'category':
            continue
        for child in category:
            if local_name(child) == 'cell' and 'number' in child.attrib:
                values[category.get('text')] = float(child.get('number'))
    return values


def compare_native(tree, name, expected):
    subtype = 'Independent Samples Test' if name == 'independent' else 'Paired Samples Test'
    tables = [node for node in tree.iter() if local_name(node) == 'pivotTable' and node.get('subType') == subtype]
    if len(tables) != 1:
        raise RuntimeError('Expected exactly one ' + subtype + ' table')
    node = tables[0]
    if name == 'independent':
        node = next(node for node in node.iter() if node.get('text') == 'Equal variances not assumed')
    actual = numeric_categories(node)
    reference = expected['independent']['welch'] if name == 'independent' else expected['paired']['test']
    keys = {'t': 't', 'df': 'df', 'Two-Sided p': 'p_two_sided', 'Lower': 'ci95_lower', 'Upper': 'ci95_upper'}
    keys.update({'Mean Difference': 'mean_difference', 'Std. Error Difference': 'se_difference'} if name == 'independent'
                else {'Mean': 'mean_difference', 'Std. Error Mean': 'se_difference'})
    for native, key in keys.items():
        if native not in actual or abs(actual[native] - reference[key]) > 1e-9:
            raise RuntimeError(f'Native {name} {native} does not match the independent reference: {actual.get(native)}')
    return {key: actual[native] for native, key in keys.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='Directory for genuine SPSS XML and text table exports.')
    args = parser.parse_args()
    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        import spss
    except ImportError as exc:
        raise SystemExit('Run this script with the Python launcher supplied by your licensed SPSS installation.') from exc
    print('Starting the installed SPSS backend in a separate session...', flush=True)
    spss.StartSPSS()
    expected = json.loads((PACKAGE_DIR / 'spss-worked-example' / 'expected_results.json').read_text(encoding='utf-8'))
    verified = {}
    try:
        for name, syntax in [
            ('independent', PACKAGE_DIR / 'ramp_hazard_training.sps'),
            ('paired', PACKAGE_DIR / 'spss-worked-example' / 'ramp_hazard_paired.sps'),
        ]:
            print('Running ' + syntax.name, flush=True)
            spss.Submit('NEW FILE.\nSET OLANG=ENGLISH.\nSET DECIMAL=DOT.')
            xml = output / (name + '.xml')
            text = output / (name + '.txt')
            spss.Submit(
                'OMS /SELECT TABLES WARNINGS /DESTINATION FORMAT=OXML OUTFILE=' + quoted(xml) + " VIEWER=NO /TAG='xml'.\n"
                'OMS /SELECT TABLES WARNINGS /DESTINATION FORMAT=TEXT OUTFILE=' + quoted(text) + " VIEWER=NO /TAG='text'."
            )
            try:
                spss.Submit(syntax.read_text(encoding='utf-8'))
            finally:
                spss.Submit('OMSEND.')
            tree = ET.parse(xml)
            tables = [node for node in tree.iter() if local_name(node) == 'pivotTable']
            warnings = [node for node in tree.iter() if local_name(node).lower() in {'warning', 'warningtext'}
                        or node.get('subType', '').lower() in {'warnings', 'errors'}]
            if not tables:
                raise RuntimeError('No SPSS result tables were exported for ' + name)
            if warnings:
                raise RuntimeError('SPSS reported warnings; inspect ' + str(xml))
            verified[name] = compare_native(tree, name, expected)
            print(name + ': ' + str(len(tables)) + ' native result tables exported to ' + str(xml), flush=True)
    finally:
        spss.StopSPSS()
    summary = {'provenance': 'Values extracted from genuine native SPSS OMS output, compared with independent references',
               'absolute_tolerance': 1e-9, 'verified': verified}
    (output / 'verified_results.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS: native differences, SE, two-sided t, df, p, and intervals match both independent references.', flush=True)


if __name__ == '__main__':
    main()
