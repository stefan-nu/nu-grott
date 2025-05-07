# Contributing to nu-grott

Contributions are highly encouraged.

Thanks to everyone who spends time and effort to improve this project.

## How to contribute

There are lots of ways to contribute to nu-grott:

- Ask and answer questions

- Report Issues

- Propose Features or Improvements

- Submit Pull Requests

- Provide test data from your growatt device




## Making changes


* Pull latest [master][master] and create a new branch:
    - Branch names should use lowercase.
    - The last part of the name can be keywords like `bugfix`, `feature`,
      `optim`, `docs`, `refactor`, `test`, etc.
    - Branches should be named after what the change is about.
    - Branches should not be named after the issue number,
      developer name, etc.

* Organize your work:
    - Specialize your branch to target one topic only.
      Split your work in multiple branches if necessary.
    - Make commits of logical units.
    - Avoid "fix-up" commits.
      Instead, rewrite your history so that the original commit is "clean".
    - Try to write a [quality commit message][commits]:
        + Separate subject line from body with a blank line.
        + Limit subject line to 50 characters.
        + Capitalize the subject line.
        + Do not end the subject line with a period.
        + Wrap the body at 72 characters.
        + Include motivation for the change
          and contrast its implementation with previous behavior.
          Explain the _what_ and _why_ instead of _how_.

* Add or update unit tests:
    - All behavioral changes should come with a unit test that verifies
      that the new feature or fixed issue works as expected.
    - Consider improving existing tests if it makes sense to do so.

* Polish your work:
    - The code should be clean, with documentation where needed.
    - respect the currently used coding style
    - respect the coding rules given below
    - The change must be complete (no upcoming fix-up commits).
    - Functional changes should always be accompanied by tests (see above).
      Changes without tests should explain why tests are not present.
      (Changes that are non-functional, such as documentation changes,
      can usually omit tests without justification.)

* Prepare a Pull Request (PR):
    - To reduce the likelihood of conflicts and test failures,
      consider rebasing your work on top of latest master before creating a PR.
    - Verify that your code is working properly
      by running the existing tests in your build directory.
    - The PR title should represent _what_ is being changed
    - The PR description should document the _why_ the change needed to be done
      and not _how_, which should be obvious by doing the code review.

[master]: https://github.com/stefan-nu/grott/tree/master
[commits]: https://chris.beams.io/posts/git-commit/


