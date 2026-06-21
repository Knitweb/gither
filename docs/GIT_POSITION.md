# Git Position

Gither does not call Git a formal open standard.

Git is open source.
The reference implementation is GPLv2 software that can be read, modified, and
distributed.

Git is also a de-facto interoperable standard.
Its object model, pack files, index format, and wire protocols are documented by the
Git project and implemented by multiple independent libraries.

That is different from a formally ratified open standard such as a W3C, IETF, ISO,
or ECMA specification.
There is no ISO Git and no IETF RFC for Git as a complete standard.

## Gither Position

Gither keeps Git as a useful low-level substrate.

Git gives:

- content-addressed objects;
- commit history;
- branches and tags;
- mature transport;
- broad tool compatibility.

Gither replaces the hosted forge layer:

- repository registry;
- issue and task routing;
- change proposals;
- review gates;
- CI receipts;
- release manifests;
- mirror policy.

## Knitweb Position

Knitweb can give Gither a stronger content-addressing foundation than Git alone when
records use published multiformats and IPLD specifications.

The target path is:

```text
Git object compatibility -> Gither review and CI state -> Knitweb signed records
```

GitHub and GitLab are allowed to mirror this state.
They are not allowed to be the only authority.
