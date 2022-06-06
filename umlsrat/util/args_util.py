import argparse


# our copy
def str2bool(v):
    """ArgumentParser doesn't support type=bool. Thus, this helper method will convert
    from possible string types to True / False."""
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")
