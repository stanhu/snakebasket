excluded_tests = [
    # Temporarily excluded until migrated to pip 1.3.x
    '-e', 'test_uninstall_namespace_package',
    # Excluded because snakebasket doesn't support Mercurial nor Subversion
    '-e', 'test_install_editable_from_hg',
    '-e', 'test_cleanup_after_install_editable_from_hg',
    '-e', 'test_freeze_mercurial_clone',
    '-e', 'test_install_dev_version_from_pypi',
    '-e', 'test_obtain_should_recognize_auth_info_in_url',
    '-e', 'test_export_should_recognize_auth_info_in_url',
    '-e', 'test_install_subversion_usersite_editable_with_setuptools_fails',
    '-e', 'test_vcs_url_final_slash_normalization',
    '-e', 'test_install_global_option_using_editable',
    '-e', 'test_install_editable_from_svn',
    '-e', 'test_download_editable_to_custom_path',
    '-e', 'test_editable_no_install_followed_by_no_download',
    '-e', 'test_create_bundle',
    '-e', 'test_cleanup_after_create_bundle',
    '-e', 'test_freeze_svn',
    '-e', 'test_multiple_requirements_files',
    '-e', 'test_uninstall_editable_from_svn',
    '-e', 'test_uninstall_from_reqs_file',
    '-e', 'test_install_subversion_usersite_editable_with_distribute',
    '-e', 'test_freeze_bazaar_clone',
    # Pip tests excluded because of different functionality in snakebasket  
    '-e', 'test_install_from_mirrors_with_specific_mirrors',
    '-e', 'test_no_upgrade_unless_requested',
    '-e', 'test_upgrade_to_specific_version',
    '-e', 'test_install_user_conflict_in_globalsite',
    '-e', 'test_install_user_conflict_in_globalsite_and_usersite',
    '-e', 'test_install_user_conflict_in_usersite',
    '-e', 'test_upgrade_user_conflict_in_globalsite',
    '-e', 'test_install_user_in_global_virtualenv_with_conflict_fails',
    # Pip tests excluded because of incompatibility with current `pip search` results format  
    '-e', 'test_search',
    '-e', 'test_multiple_search'
]
