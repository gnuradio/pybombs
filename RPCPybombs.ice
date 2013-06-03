module RPCPybombs {

    struct PkgInfo {
        string name;
        string category;
        bool installed;
        string satisfier;
        string version;
        string source;
    };

    sequence<PkgInfo> PkgInfoSeq;
    sequence<string> PkgNameSeq;

    interface Manager {
        PkgInfoSeq list(PkgNameSeq pkglist);
        int install(PkgNameSeq pkglist);
        int remove(PkgNameSeq pkglist);
        int rnd(PkgNameSeq pkglist);
        int update(PkgNameSeq pkglist);
        string status(int oid);
    };

};

