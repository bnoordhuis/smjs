{
  'variables': {
    'target_arch%': 'x64',
  },

  'target_defaults': {
    'default_configuration': 'Release',

    'configurations': {
      'Debug': {
        'cflags': [ '-g', '-O0' ],
      },
      'Release': {
        'defines': [ 'NDEBUG' ],
        'cflags': [ '-O3', '-fno-strict-aliasing' ],
      },
    },

    'include_dirs': [
      '<(SHARED_INTERMEDIATE_DIR)',
      'config/common',
      'js/src',
      'js/src/assembler',
      'js/src/methodjit',
    ],

    'defines': [
      'HAVE_VA_LIST_AS_ARRAY=0', # XXX arch/platform/ABI/compiler dependent...
      '__STDC_LIMIT_MACROS=1',
      'JS_MONOIC=1',
      'JS_POLYIC=1',
      'JS_METHODJIT=1',
      'JS_DEFAULT_JITREPORT_GRANULARITY=3',
    ],

    # XXX I have frankly no idea what JS_NUNBOX32 and JS_PUNBOX64 *really* do
    'conditions': [
      ['target_arch == "x64"', {
        'defines': [
          'JS_BITS_PER_WORD_LOG2=6',
          'JS_BYTES_PER_WORD=8',
          'JS_PUNBOX64=1',
          'JS_CPU_X64=1',
        ],
      }],
      ['target_arch == "ia32"', {
        'defines': [
          'JS_BITS_PER_WORD_LOG2=5',
          'JS_BYTES_PER_WORD=4',
          'JS_NUNBOX32=1',
          'JS_CPU_X86=1',
        ],
      }],
      ['target_arch == "arm"', {
        'defines': [
          'JS_BITS_PER_WORD_LOG2=5',
          'JS_BYTES_PER_WORD=4',
          'JS_NUNBOX32=1',
          'JS_CPU_ARM=1',
        ],
      }],
      ['OS == "linux"', {
        'include_dirs': [ 'config/linux' ],
        'defines': [ 'JS_HAVE_ENDIAN_H=1' ],
      }],
      ['OS == "mac"', {
        'include_dirs': [ 'config/darwin' ],
        'defines': [
          'JS_HAVE_MACHINE_ENDIAN_H=1',
          'XP_MACOSX=1',
          'DARWIN=1',
        ],
        'conditions': [
          ['target_arch == "x64"', {
            'xcode_settings': {'ARCHS': [ 'x86_64' ]},
          }],
          ['target_arch == "ia32"', {
            'xcode_settings': {'ARCHS': [ 'i386' ]},
          }],
        ],
      }],
      ['OS == "win"', {
        'include_dirs': [ 'config/windows' ],
        'defines': [ 'XP_WIN=1' ],
      }, {
        'cflags': [
          # -Wno-invalid-offsetof disables warnings when offsetof() is used
          # on non-POD types. This is obviously the wrong thing to do but the
          # warnings drown out everything else....
          '-Wno-invalid-offsetof',
          '-pthread',
        ],
        'defines': [
          'XP_UNIX=1',
        ],
        'libraries': [
          '-pthread',
        ],
      }],
    ],
  },

  'targets': [
    {
      'target_name': 'shell',
      'type': 'executable',
      'dependencies': [ 'smjs' ],
      'include_dirs': [
        'js/src/shell',
        'js/src/perf',
      ],
      'sources': [
        'js/src/shell/js.cpp',
        'js/src/shell/jsheaptools.cpp',
        'js/src/shell/jsoptparse.cpp',
        'js/src/shell/jsworkers.cpp',
      ],
    },

    {
      'target_name': 'jskwgen',
      'type': 'executable',
      'sources': [ 'js/src/jskwgen.cpp' ],
    },

    {
      'target_name': 'jsoplengen',
      'type': 'executable',
      'sources': [ 'js/src/jsoplengen.cpp' ],
    },

    {
      'target_name': 'smjs',
      'type': 'static_library',

      'dependencies': [
        'jskwgen',
        'jsoplengen',
      ],

      'actions': [
        {
          'action_name': 'jskwgen',
          'inputs': [
            '<(PRODUCT_DIR)/<(EXECUTABLE_PREFIX)jskwgen<(EXECUTABLE_SUFFIX)',
          ],
          'outputs': [
            '<(SHARED_INTERMEDIATE_DIR)/jsautokw.h',
          ],
          'action': [
            '<@(_inputs)',
            '<@(_outputs)',
          ],
        },
        {
          'action_name': 'jsoplengen',
          'inputs': [
            '<(PRODUCT_DIR)/<(EXECUTABLE_PREFIX)jsoplengen<(EXECUTABLE_SUFFIX)',
          ],
          'outputs': [
            '<(SHARED_INTERMEDIATE_DIR)/jsautooplen.h',
          ],
          'action': [
            '<@(_inputs)',
            '<@(_outputs)',
          ],
        },
      ],

      'conditions': [
        ['OS == "win"', {
          'sources': [
            'js/src/assembler/jit/ExecutableAllocatorWin.cpp',
            'js/src/yarr/OSAllocatorPosix.cpp',
          ],
        }, {
          'sources': [
            'js/src/assembler/jit/ExecutableAllocatorPosix.cpp',
            'js/src/yarr/OSAllocatorPosix.cpp',
          ],
        }],
        ['OS == "linux"', {
          'sources': [ 'js/src/perf/pm_linux.cpp' ],
        }, {
          'sources': [ 'js/src/perf/pm_stub.cpp' ],
        }],
      ],

      'sources': [
        'compat/compat.cpp',
        'js/src/MemoryMetrics.cpp',
        'js/src/assembler/assembler/MacroAssemblerX86Common.cpp',
        'js/src/assembler/jit/ExecutableAllocator.cpp',
        'js/src/builtin/MapObject.cpp',
        'js/src/builtin/RegExp.cpp',
        'js/src/builtin/TestingFunctions.cpp',
        'js/src/ds/LifoAlloc.cpp',
        'js/src/frontend/BytecodeCompiler.cpp',
        'js/src/frontend/BytecodeEmitter.cpp',
        'js/src/frontend/FoldConstants.cpp',
        'js/src/frontend/ParseMaps.cpp',
        'js/src/frontend/ParseNode.cpp',
        'js/src/frontend/Parser.cpp',
        'js/src/frontend/SemanticAnalysis.cpp',
        'js/src/frontend/TokenStream.cpp',
        'js/src/gc/Memory.cpp',
        'js/src/gc/Statistics.cpp',
        'js/src/jsalloc.cpp',
        'js/src/jsanalyze.cpp',
        'js/src/jsapi.cpp',
        'js/src/jsarray.cpp',
        'js/src/jsatom.cpp',
        'js/src/jsbool.cpp',
        'js/src/jsclone.cpp',
        'js/src/jscntxt.cpp',
        'js/src/jscompartment.cpp',
        'js/src/jscrashreport.cpp',
        'js/src/jsdate.cpp',
        'js/src/jsdbgapi.cpp',
        'js/src/jsdhash.cpp',
        'js/src/jsdtoa.cpp',
        'js/src/jsexn.cpp',
        'js/src/jsfriendapi.cpp',
        'js/src/jsfun.cpp',
        'js/src/jsgc.cpp',
        'js/src/jsgcmark.cpp',
        'js/src/jshash.cpp',
        'js/src/jsinfer.cpp',
        'js/src/jsinterp.cpp',
        'js/src/jsiter.cpp',
        'js/src/jslog2.cpp',
        'js/src/jsmath.cpp',
        'js/src/jsnativestack.cpp',
        'js/src/jsnum.cpp',
        'js/src/jsobj.cpp',
        'js/src/json.cpp',
        'js/src/jsonparser.cpp',
        'js/src/jsopcode.cpp',
        'js/src/jsprf.cpp',
        'js/src/jsprobes.cpp',
        'js/src/jspropertycache.cpp',
        'js/src/jspropertytree.cpp',
        'js/src/jsproxy.cpp',
        'js/src/jsreflect.cpp',
        'js/src/jsscope.cpp',
        'js/src/jsscript.cpp',
        'js/src/jsstr.cpp',
        'js/src/jstypedarray.cpp',
        'js/src/jsutil.cpp',
        'js/src/jswatchpoint.cpp',
        'js/src/jsweakmap.cpp',
        'js/src/jswrapper.cpp',
        'js/src/jsxdrapi.cpp',
        'js/src/jsxml.cpp',
        'js/src/methodjit/Compiler.cpp',
        'js/src/methodjit/FastArithmetic.cpp',
        'js/src/methodjit/FastBuiltins.cpp',
        'js/src/methodjit/FastOps.cpp',
        'js/src/methodjit/FrameState.cpp',
        'js/src/methodjit/ImmutableSync.cpp',
        'js/src/methodjit/InvokeHelpers.cpp',
        'js/src/methodjit/Logging.cpp',
        'js/src/methodjit/LoopState.cpp',
        'js/src/methodjit/MethodJIT.cpp',
        'js/src/methodjit/MonoIC.cpp',
        'js/src/methodjit/PolyIC.cpp',
        'js/src/methodjit/Retcon.cpp',
        'js/src/methodjit/StubCalls.cpp',
        'js/src/methodjit/StubCompiler.cpp',
        'js/src/methodjit/TrampolineCompiler.cpp',
        'js/src/perf/jsperf.cpp',
        'js/src/prmjtime.cpp',
        'js/src/sharkctl.cpp',
        'js/src/v8-dtoa/checks.cc',
        'js/src/v8-dtoa/conversions.cc',
        'js/src/v8-dtoa/diy-fp.cc',
        'js/src/v8-dtoa/fast-dtoa.cc',
        'js/src/v8-dtoa/platform.cc',
        'js/src/v8-dtoa/utils.cc',
        'js/src/v8-dtoa/v8-dtoa.cc',
        'js/src/vm/Debugger.cpp',
        'js/src/vm/GlobalObject.cpp',
        'js/src/vm/MethodGuard.cpp',
        'js/src/vm/ObjectImpl.cpp',
        'js/src/vm/RegExpObject.cpp',
        'js/src/vm/RegExpStatics.cpp',
        'js/src/vm/ScopeObject.cpp',
        'js/src/vm/Stack.cpp',
        'js/src/vm/String.cpp',
        'js/src/vm/StringBuffer.cpp',
        'js/src/vm/Unicode.cpp',
        'js/src/yarr/PageBlock.cpp',
        'js/src/yarr/YarrInterpreter.cpp',
        'js/src/yarr/YarrJIT.cpp',
        'js/src/yarr/YarrPattern.cpp',
        'js/src/yarr/YarrSyntaxChecker.cpp',
      ],
    },
  ],
}
