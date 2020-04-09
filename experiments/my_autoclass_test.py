from collections import defaultdict

import jnius_config
jnius_config.set_classpath(
    '.', '/home/jim/Projects/git/processing/core/library/*')
from jnius import autoclass, JavaClass, JavaStaticMethod, MetaJavaClass, find_javaclass, with_metaclass  # noqa


# some stuff copied from jnius/reflect.py
def get_signature(cls_tp):
    tp = cls_tp.getName()
    if tp[0] == '[':
        return tp.replace('.', '/')
    signatures = {
        'void': 'V', 'boolean': 'Z', 'byte': 'B',
        'char': 'C', 'short': 'S', 'int': 'I',
        'long': 'J', 'float': 'F', 'double': 'D'}
    ret = signatures.get(tp)
    if ret:
        return ret
    # don't do it in recursive way for the moment,
    # error on the JNI/android: JNI ERROR (app bug): local reference table
    # overflow (max=512)

    # ensureclass(tp)
    return 'L{0};'.format(tp.replace('.', '/'))


class Modifier(with_metaclass(MetaJavaClass, JavaClass)):
    __javaclass__ = 'java/lang/reflect/Modifier'

    isAbstract = JavaStaticMethod('(I)Z')
    isFinal = JavaStaticMethod('(I)Z')
    isInterface = JavaStaticMethod('(I)Z')
    isNative = JavaStaticMethod('(I)Z')
    isPrivate = JavaStaticMethod('(I)Z')
    isProtected = JavaStaticMethod('(I)Z')
    isPublic = JavaStaticMethod('(I)Z')
    isStatic = JavaStaticMethod('(I)Z')
    isStrict = JavaStaticMethod('(I)Z')
    isSynchronized = JavaStaticMethod('(I)Z')
    isTransient = JavaStaticMethod('(I)Z')
    isVolatile = JavaStaticMethod('(I)Z')


PythonPApplet = autoclass('processing.core.PythonPApplet')
_papplet = PythonPApplet()

cls = find_javaclass('processing.core.PythonPApplet')

methods = defaultdict(set)
fields = defaultdict(set)

while cls is not None:
    print(cls.getName())
    print("=" * 20)
    method_list = []
    for method in cls.getDeclaredMethods():
        name = method.getName()
        modifiers = method.getModifiers()

        static = Modifier.isStatic(modifiers)
        public = Modifier.isPublic(modifiers)
        varargs = method.isVarArgs()
        sig = '({0}){1}'.format(''.join([get_signature(x) for x in method.getParameterTypes()]),
                                get_signature(method.getReturnType()))
        methods[name].add((sig, static, public, varargs))
        method_list.append((name, sig, static, public, varargs))

    # if method_list:
    #     print('methods')
    #     print("-" * 20)
    #     for m in method_list:
    #         print(*m)

    fields_list = []
    for field in cls.getDeclaredFields():
        name = field.getName()
        modifiers = field.getModifiers()

        static = Modifier.isStatic(modifiers)
        public = Modifier.isPublic(modifiers)
        type_ = get_signature(field.getType())
        val = None
        if static:
            if hasattr(PythonPApplet, name):
                val = getattr(PythonPApplet, name)
            else:
                # TODO: this should not be
                print(f'skipping {name}')
        fields[name].add((name, type_, val, static, public))
        fields_list.append((name, type_, val, static, public))

    # if fields_list:
    #     print('fields')
    #     print("-" * 20)
    #     for f in fields_list:
    #         print(*f)

    _cls = cls.getSuperclass()
    if not _cls and cls.isInterface():
        cls = find_javaclass('java.lang.Object')
    else:
        cls = _cls

    print('\n')
