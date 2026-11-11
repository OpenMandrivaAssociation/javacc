Name:		javacc
Version:	7.0.12
Release:	1
Summary:	Parser generator for Java
Group:		Development/Java
License:	BSD-3-Clause
URL:		https://javacc.github.io/javacc/
# Generated parser sources from the 7.0.12 sources jar, plus the
# Sun BSD LICENSE from the git tag. The git tag bootstraps those
# sources from a prebuilt jar, which this archive does not contain.
Source0:	javacc-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
Requires:	java

%description
JavaCC %{version} reads a grammar and writes a Java parser.
FreeMarker 2.3.35 generates its FTL parser with this release.
The jar also contains the JJTree and JJDoc tools and the
templates those generators load at runtime.

%prep
%autosetup -n javacc-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
# The four default-package launchers keep the jar from being a module.
# The wrappers call org.javacc.parser.Main, jjtree.Main, and JJDocMain.
find src/main/java -name '*.java' \
	! -name 'JavaCCInterpreter.java' \
	! -name 'javacc.java' \
	! -name 'jjdoc.java' \
	! -name 'jjtree.java' > sources.list
test "$(wc -l < sources.list)" -eq 160
mkdir -p classes
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
	-d classes @sources.list
cp -a templates classes/templates
cp -a version.properties classes/version.properties
printf 'Manifest-Version: 1.0\nAutomatic-Module-Name: org.javacc\n\n' > manifest.mf
jar cfm javacc.jar manifest.mf -C classes .
jar i javacc.jar
jar tf javacc.jar | grep -F -q 'templates/TokenManagerBoilerPlateMethods.template'
jar tf javacc.jar | grep -qx 'version.properties'
jar tf javacc.jar | grep -F -q 'org/javacc/parser/Main.class'

cat > javacc.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>net.java.dev.javacc</groupId>
  <artifactId>javacc</artifactId>
  <version>7.0.12</version>
  <name>JavaCC</name>
  <description>Java Compiler Compiler 7.0.12 parser generator.</description>
  <url>https://javacc.github.io/javacc/</url>
  <licenses>
    <license>
      <name>BSD-3-Clause</name>
      <url>https://raw.githubusercontent.com/javacc/javacc/javacc-7.0.12/LICENSE</url>
    </license>
  </licenses>
</project>
EOF

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact javacc.pom:javacc.jar \
	--file-name javacc \
	--filelist .mfiles
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/javacc << 'EOF'
#!/bin/sh
JAVA_HOME="${JAVA_HOME:-%{_jvmdir}/java-openjdk}"
exec "$JAVA_HOME/bin/java" -cp "%{_javadir}/javacc.jar" org.javacc.parser.Main "$@"
EOF
cat > %{buildroot}%{_bindir}/jjtree << 'EOF'
#!/bin/sh
JAVA_HOME="${JAVA_HOME:-%{_jvmdir}/java-openjdk}"
exec "$JAVA_HOME/bin/java" -cp "%{_javadir}/javacc.jar" org.javacc.jjtree.Main "$@"
EOF
cat > %{buildroot}%{_bindir}/jjdoc << 'EOF'
#!/bin/sh
JAVA_HOME="${JAVA_HOME:-%{_jvmdir}/java-openjdk}"
exec "$JAVA_HOME/bin/java" -cp "%{_javadir}/javacc.jar" org.javacc.jjdoc.JJDocMain "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/javacc %{buildroot}%{_bindir}/jjtree %{buildroot}%{_bindir}/jjdoc
echo "%{_bindir}/javacc" >> .mfiles
echo "%{_bindir}/jjtree" >> .mfiles
echo "%{_bindir}/jjdoc" >> .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/javacc.jar
test -s "$JAR"
mkdir -p check/gen
cat > check/Hello.jj << 'END'
options { STATIC = false; }
PARSER_BEGIN(Hello)
public class Hello {
	public static void main(String[] args) throws Exception {
		Hello p = new Hello(new java.io.StringReader("gradle"));
		p.Input();
		System.out.println("javacc_ok gradle");
	}
}
PARSER_END(Hello)
TOKEN : { <GRADLE : "gradle"> }
void Input() : {} { <GRADLE> <EOF> }
END
java -cp "$JAR" org.javacc.parser.Main -OUTPUT_DIRECTORY=check/gen check/Hello.jj > check/gen.log
cat check/gen.log
grep -F -q "Java Compiler Compiler Version %{version}" check/gen.log
grep -F -q 'Parser generated successfully.' check/gen.log
javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none -d check/gen check/gen/*.java
java -cp check/gen Hello > check/out.txt
cat check/out.txt
grep -F -q 'javacc_ok gradle' check/out.txt

%files -f .mfiles
%doc LICENSE
