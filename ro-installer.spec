Name:           ro-installer
Version:        1.0.0
Release:        1%{?dist}
Summary:        ro-ASD Operating System Installer
License:        GPLv3
URL:            https://github.com/Acik-Kaynak-Gelistirme-Toplulugu/ro-Installer
VCS:            {{{ git_dir_vcs }}}
Source0:        {{{ git_dir_pack }}}
BuildArch:      noarch

Requires:       python3, python3-pyqt6, python3-pyqt6-webengine, parted, dosfstools, e2fsprogs, btrfs-progs, xfsprogs, rsync, kpmcore, squashfs-tools, polkit

%description
ro-ASD Operating System Installer built with PyQt6 WebEngine and modern web UI technologies.

%prep
{{{ git_dir_setup_macro }}}

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/share/ro-installer
cp -r * $RPM_BUILD_ROOT/usr/share/ro-installer/

# Bin wrapper script
mkdir -p $RPM_BUILD_ROOT/usr/bin
cat << 'EOF' > $RPM_BUILD_ROOT/usr/bin/ro-installer
#!/bin/bash
if [ "$EUID" -ne 0 ]; then
    xhost +SI:localuser:root >/dev/null 2>&1
    if sudo -n true 2>/dev/null; then
        exec sudo -E env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" WAYLAND_DISPLAY="$WAYLAND_DISPLAY" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" QT_QPA_PLATFORM=xcb LIBGL_ALWAYS_SOFTWARE=1 "$0" "$@"
    else
        exec pkexec env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" WAYLAND_DISPLAY="$WAYLAND_DISPLAY" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" QT_QPA_PLATFORM=xcb LIBGL_ALWAYS_SOFTWARE=1 "$0" "$@"
    fi
fi

export PYTHONPATH=/usr/share/ro-installer
exec python3 /usr/share/ro-installer/main.py "$@"
EOF
chmod +x $RPM_BUILD_ROOT/usr/bin/ro-installer

# Application Desktop Shortcut (App Menu)
mkdir -p $RPM_BUILD_ROOT/usr/share/applications
cat << 'EOF' > $RPM_BUILD_ROOT/usr/share/applications/ro-installer.desktop
[Desktop Entry]
Name=ro-Installer
Comment=Install ro-ASD Operating System
Exec=/usr/bin/ro-installer
Icon=drive-harddisk
Terminal=false
Type=Application
Categories=System;Utility;
EOF


# Polkit policy (pkexec without password prompt for live environment, or with prompt generally)
mkdir -p $RPM_BUILD_ROOT/usr/share/polkit-1/actions
cat <<EOF > $RPM_BUILD_ROOT/usr/share/polkit-1/actions/org.ro-asd.installer.policy
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <action id="org.ro-asd.installer.pkexec.run">
    <description>Run ro-Installer as root</description>
    <message>Authentication is required to run the ro-ASD Installer</message>
    <defaults>
      <allow_any>yes</allow_any>
      <allow_inactive>yes</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/bin/ro-installer</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>
</policyconfig>
EOF

%files
/usr/share/ro-installer/
/usr/bin/ro-installer
/usr/share/applications/ro-installer.desktop
/usr/share/polkit-1/actions/org.ro-asd.installer.policy

%changelog
* Mon Feb 23 2026 ro-ASD Project <info@ro-asd.org> - 1.0.0-1
- Initial release of ro-Installer as an RPM package
