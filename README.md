# T2Tools

Tools to work with the MIT Tier-2 storage from remote.

The Tier-2 storage is a Ceph filesystem POSIX mounted on a storage server. All operations are
executed through ssh on that server (see `config/t2tools.cfg`):

    server : t2dsk0014.cmsaf.mit.edu   (user paus)
    root   : /ceph/tier2mit/rootfolder (logical /cms/store/... is root + /cms/store/...)

Tools always use the logical name space (`/cms/store/...`). Also accepted as input are
`root://<server>//store/...`, `/mnt/hadoop/cms/...` (legacy) and the physical path.

The previous HDFS based version is tagged `hdfs-legacy` (maintenance branch `hdfs-legacy`).

## Install

    ./install.sh                  # generates setup.sh
    source setup.sh

## Usage

    t2tools.py --action=<action> --source=<path> [ --target=<path> ] [ --options=<opt> ] [ --debug=N ]

| action    | what                                                   |
|-----------|--------------------------------------------------------|
| `ls`      | list (`F:<size> <path>` / `D:0 <path>`, `--options=-l` long format), globs allowed |
| `du`      | size of each entry in a directory (`<size>  <path>`), nothing for empty directory |
| `test`    | exit code 0 if path exists                             |
| `testDir` | exit code 0 if path is a directory                     |
| `rm`      | remove file                                            |
| `rmr`     | remove recursively (refused above `minRmrDepth` levels) |
| `rmdir`   | remove empty directory                                 |
| `mkdir`   | make directory (`--options=-p`)                        |
| `chmod`   | change permissions (`--options="-R a+r"`)              |
| `cp`,`mv` | copy/move on the Tier-2                                |
| `up`      | upload local file `--source` to Tier-2 `--target`      |
| `down`    | download Tier-2 `--source` to local `--target`         |

Uploads/downloads go through a `.partial` file and use scp via the server (`transfer = ssh`) or
xrdcp (`transfer = xrootd`).

Convenience wrappers: `list`, `remove [--catalog]`, `removedir`, `makedir [--p]`, `move`,
`changemod --options=...`, `upload`.
