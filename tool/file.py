import os


def get_file_suffix(filename: str) -> str:
    suffix = ""
    for i, c in enumerate(filename[::-1]):
        suffix += c
        if c == ".":
            suffix = filename[len(filename) - (i + 1):]
            break
    
    return suffix


def get_dir_all_file_path(
        dir_path: str, 
        exclude_names: None| list[str] | tuple[str] = None, 
        file_specify_suffixs: None | list[str] | tuple[str] = None,
        exclude_like_names: None | list[str] | tuple[str] | str = None,
) -> list:
    file_paths = []
    if not os.path.isdir(dir_path):
        return file_paths
    
    if exclude_names is None:
        exclude_names = []

    if file_specify_suffixs is None:
        file_specify_suffixs = []
    
    if exclude_like_names is None:
        exclude_like_names = []
    
    dir_paths = [dir_path]
    while dir_paths:
        path = dir_paths.pop()
        filenames = os.listdir(path)
        for filename in filenames:
            if filename in exclude_names:
                continue
            is_continue = False
            for e_name in exclude_like_names:
                if e_name in filename:
                    is_continue = True
                    break
            if is_continue:
                continue
            file_path = os.path.join(path, filename)
            if os.path.isdir(file_path):
                dir_paths.append(file_path)
            elif os.path.isfile(file_path):
                suffix = get_file_suffix(filename)
                if suffix and suffix.lower() not in file_specify_suffixs:
                    continue
                file_paths.append(file_path)
            else:
                raise

    return file_paths


if __name__ == "__main__":
    print(get_file_suffix(".aaaaaaaaaa.sift"))