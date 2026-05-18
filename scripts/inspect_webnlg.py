"""Inspect WebNLG parquet fields.

Run from project root:
  python scripts_inspect_webnlg.py
"""

from lemon_factor.datasets.webnlg_loader import load_webnlg_parquet


def main() -> None:
    ds = load_webnlg_parquet("en")
    print(ds)
    print(ds.keys())
    print(ds["train"].features)
    print(ds["train"][0])


if __name__ == "__main__":
    main()
