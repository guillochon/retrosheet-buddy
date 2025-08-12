from pathlib import Path

from retrosheet_buddy.parser import parse_event_file
from retrosheet_buddy.writer import write_event_file


def test_retains_sub_and_data_on_save(tmp_path: Path) -> None:
    # Use provided sample file with sub and data lines
    input_path = Path("sample_data/SDN198205020.EVN")
    assert input_path.exists(), "Expected sample input file to exist"

    event_file = parse_event_file(input_path)

    # Write to a temp path
    out_path = tmp_path / "SDN198205020.EVN"
    write_event_file(event_file, out_path)

    text = out_path.read_text(encoding="utf-8")
    # Verify representative 'sub' lines are present
    assert 'sub,flant001,"Tim Flannery",1,9,11' in text
    assert 'sub,showe001,"Eric Show",1,9,1' in text
    assert 'sub,dernb001,"Bob Dernier",0,1,9' in text
    assert 'sub,grosg001,"Greg Gross",0,3,7' in text
    assert 'sub,edwad101,"Dave Edwards",1,9,11' in text

    # Verify 'data' lines are present
    assert "data,er,krukm001,0" in text
    assert "data,er,curtj001,3" in text
    assert "data,er,showe001,0" in text
