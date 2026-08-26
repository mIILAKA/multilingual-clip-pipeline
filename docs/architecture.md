# Architecture and design decisions

## 1. Public boundary

The production workspace contains source media, derived frames, transcripts, channel analytics,
speaker profiles, publishing metadata, and credentials stored outside the repository. None of those
belong in a recruiting sample.

This public edition therefore keeps only three transferable ideas:

1. a small, explicit data model for cuts and subtitles;
2. deterministic validation that has no media or network dependency;
3. a workflow in which final rendering is unavailable until human review is approved;
4. an FFmpeg E2E path that renders only synthetic media.

The included example is synthetic. File paths and dialogue do not refer to a real creator or video.

## 2. Deterministic core, replaceable edges

Validation functions receive immutable data and return issues. They do not read environment
variables, call a model, invoke FFmpeg, or mutate project files. This makes failures reproducible and
keeps model inference and rendering at the edges of the system.

```text
ASR / diarization / translation
                  ↓ adapters
          Project data model
                  ↓
     deterministic validation core
                  ↓
       review and publishing gates
                  ↓
       FFmpeg rendering adapter
```

## 3. Why visual width is used

Counting Unicode code points gives misleading reading speeds for multilingual subtitles. In this
public version, full-width characters count as 1.0 and half-width characters as 0.5. The production
system uses the same principle so that an Indonesian or English line is not judged as if every Latin
character occupied the width of a Japanese character.

## 4. Why human review is a first-class stage

A validator can prove that a subtitle is on screen long enough. It cannot prove that a translation is
faithful, that a joke still works after editing, or that a clip represents the speaker respectfully.
The workflow therefore treats machine validation as necessary but insufficient.

The default plan stops after `human-review`. `render-final` and `sync-manifest` are added only when
`approved_for_final=True` is explicit.

## 5. Synthetic E2E rendering

The public renderer deliberately supports one source file. This keeps the example small while still
proving that structured cut data controls a real media operation. The demo:

1. creates a test-pattern video and sine-wave audio using FFmpeg filters;
2. trims every requested interval with independent timestamps;
3. concatenates video and audio in the declared order;
4. uses ffprobe to verify the final duration.

No remote content is downloaded. Generated media is ignored by Git.

## 6. Failure strategy

- Structural errors are returned as stable issue codes.
- Independent errors are collected in one pass so the editor can fix them together.
- Final rendering is gated instead of relying on a warning message.
- Tests include both a clean public example and a project with multiple simultaneous failures.
- An integration test renders a real MP4 and checks its duration within an encoding tolerance.
