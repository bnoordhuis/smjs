{
  'variables': {
    'target_arch%': 'x64',
  },

  'target_defaults': {
    'default_configuration': 'Release',

    'configurations': {
      'Debug': {
        'cflags': ['-g', '-O0'],
      },
      'Release': {
        'defines': ['NDEBUG'],
        'cflags': ['-O3', '-fno-strict-aliasing'],
      },
    },

    # XXX not everything needs to be exported in direct_dependent_settings
    'direct_dependent_settings': {
      'include_dirs': [
        '<(SHARED_INTERMEDIATE_DIR)',
        'extra/mozilla/double-conversion',
        'extra/',
        'src',
        'src/assembler',
        'src/methodjit',
      ],

      'defines': [
        'HAVE_VA_LIST_AS_ARRAY=1', # XXX arch/platform/ABI/compiler dependent...
        '__STDC_LIMIT_MACROS=1',
        'JS_MONOIC=1',
        'JS_POLYIC=1',
        'JS_METHODJIT=1',
        'JS_DEFAULT_JITREPORT_GRANULARITY=3',
        'JSGC_INCREMENTAL=1',
        'IMPL_MFBT=1',
        # This implies building a static library
        'STATIC_JS_API=1',
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
          'defines': ['JS_HAVE_ENDIAN_H=1'],
        }],
        ['OS == "mac"', {
          'defines': [
            'JS_HAVE_MACHINE_ENDIAN_H=1',
            'XP_MACOSX=1',
            'DARWIN=1',
          ],
          'conditions': [
            ['target_arch == "x64"', {
              'xcode_settings': {'ARCHS': ['x86_64']},
            }],
            ['target_arch == "ia32"', {
              'xcode_settings': {'ARCHS': ['i386']},
            }],
          ],
        }],
        ['OS == "win"', {
          'defines': [
            'WIN32=1',
            'XP_WIN=1',
            'HAVE_GETSYSTEMTIMEASFILETIME=1',
            'HAVE_SYSTEMTIMETOFILETIME=1',
            'WIN32_LEAN_AND_MEAN=1',
          ],
          'conditions': [
            ['target_arch == "ia32"', {
              'defines': [
                '_X86_=1'
              ],
            }],
            ['target_arch == "x64"', {
              'defines': [
                '_AMD64_=1',
                '_M_AMD64_=1'
              ],
            }],
          ],
          'msvs_cygwin_shell': 0, # don't use bash
          'msvc_disable_warnings': [
            '4800', # warning C4800: 'variable' : forcing value to bool 'true' or
                    # 'false' (performance warning)
          ],
          'msvs_settings': {
            'VCCLCompilerTool': {
              'AdditionalOptions': [
                '/MP', # compile across multiple CPUs
              ],
            },
          }
        }, {
          'cflags': ['-pthread'],
          'defines': ['XP_UNIX=1'],
          'libraries': ['-pthread'],
        }],
      ],
    },
  },

  'targets': [
    {
      'target_name': 'shell',
      'type': 'executable',
      'dependencies': ['smjs'],
      'include_dirs': [
        'src/shell',
        'src/perf',
      ],
      'sources': [
        'src/shell/js.cpp',
        'src/shell/jsheaptools.cpp',
        'src/shell/jsoptparse.cpp',
        'src/shell/jsworkers.cpp',
      ],
    },

    {
      'target_name': 'jskwgen',
      'type': 'executable',
      'sources': ['src/jskwgen.cpp'],
    },

    {
      'target_name': 'jsoplengen',
      'type': 'executable',
      'sources': ['src/jsoplengen.cpp'],
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
          'link_settings':  {
            'libraries': [ '-lwinmm.lib' ],
          },
          'sources': [
            'src/assembler/jit/ExecutableAllocatorWin.cpp',
            'src/yarr/OSAllocatorWin.cpp',
          ],
        }, {
          'sources': [
            'src/assembler/jit/ExecutableAllocatorPosix.cpp',
            'src/yarr/OSAllocatorPosix.cpp',
          ],
        }],
        ['OS == "linux"', {
          'sources': ['src/perf/pm_linux.cpp'],
        }, {
          'sources': ['src/perf/pm_stub.cpp'],
        }],
      ],

      'sources': [
        'compat/compat.cpp',
        'extra/mozilla/double-conversion/bignum.cc',
        'extra/mozilla/double-conversion/bignum-dtoa.cc',
        'extra/mozilla/double-conversion/cached-powers.cc',
        'extra/mozilla/double-conversion/diy-fp.cc',
        'extra/mozilla/double-conversion/double-conversion.cc',
        'extra/mozilla/double-conversion/fast-dtoa.cc',
        'extra/mozilla/double-conversion/fixed-dtoa.cc',
        'extra/mozilla/double-conversion/strtod.cc',
        'src/MemoryMetrics.cpp',
        'src/assembler/assembler/MacroAssemblerX86Common.cpp',
        'src/assembler/jit/ExecutableAllocator.cpp',
        'src/builtin/MapObject.cpp',
        'src/builtin/RegExp.cpp',
        'src/builtin/TestingFunctions.cpp',
        'src/ds/LifoAlloc.cpp',
        'src/frontend/BytecodeCompiler.cpp',
        'src/frontend/BytecodeEmitter.cpp',
        'src/frontend/FoldConstants.cpp',
        'src/frontend/ParseMaps.cpp',
        'src/frontend/ParseNode.cpp',
        'src/frontend/Parser.cpp',
        'src/frontend/SemanticAnalysis.cpp',
        'src/frontend/TokenStream.cpp',
        'src/frontend/TreeContext.cpp',
        'src/gc/Marking.cpp',
        'src/gc/Memory.cpp',
        'src/gc/Statistics.cpp',
        'src/jsalloc.cpp',
        'src/jsanalyze.cpp',
        'src/jsapi.cpp',
        'src/jsarray.cpp',
        'src/jsatom.cpp',
        'src/jsbool.cpp',
        'src/jsclone.cpp',
        'src/jscntxt.cpp',
        'src/jscompartment.cpp',
        'src/jscrashreport.cpp',
        'src/jsdate.cpp',
        'src/jsdbgapi.cpp',
        'src/jsdhash.cpp',
        'src/jsdtoa.cpp',
        'src/jsexn.cpp',
        'src/jsfriendapi.cpp',
        'src/jsfun.cpp',
        'src/jsgc.cpp',
        'src/jshash.cpp',
        'src/jsinfer.cpp',
        'src/jsinterp.cpp',
        'src/jsiter.cpp',
        'src/jslog2.cpp',
        'src/jsmath.cpp',
        'src/jsnativestack.cpp',
        'src/jsnum.cpp',
        'src/jsobj.cpp',
        'src/json.cpp',
        'src/jsonparser.cpp',
        'src/jsopcode.cpp',
        'src/jsprf.cpp',
        'src/jsprobes.cpp',
        'src/jspropertycache.cpp',
        'src/jspropertytree.cpp',
        'src/jsproxy.cpp',
        'src/jsreflect.cpp',
        'src/jsscope.cpp',
        'src/jsscript.cpp',
        'src/jsstr.cpp',
        'src/jstypedarray.cpp',
        'src/jsutil.cpp',
        'src/jswatchpoint.cpp',
        'src/jsweakmap.cpp',
        'src/jswrapper.cpp',
        'src/jsxml.cpp',
        'src/methodjit/Compiler.cpp',
        'src/methodjit/FastArithmetic.cpp',
        'src/methodjit/FastBuiltins.cpp',
        'src/methodjit/FastOps.cpp',
        'src/methodjit/FrameState.cpp',
        'src/methodjit/ImmutableSync.cpp',
        'src/methodjit/InvokeHelpers.cpp',
        'src/methodjit/Logging.cpp',
        'src/methodjit/LoopState.cpp',
        'src/methodjit/MethodJIT.cpp',
        'src/methodjit/MonoIC.cpp',
        'src/methodjit/PolyIC.cpp',
        'src/methodjit/Retcon.cpp',
        'src/methodjit/StubCalls.cpp',
        'src/methodjit/StubCompiler.cpp',
        'src/methodjit/TrampolineCompiler.cpp',
        'src/perf/jsperf.cpp',
        'src/prmjtime.cpp',
        'src/sharkctl.cpp',
        'src/vm/ArgumentsObject.cpp',
        'src/vm/Debugger.cpp',
        'src/vm/GlobalObject.cpp',
        'src/vm/MethodGuard.cpp',
        'src/vm/ObjectImpl.cpp',
        'src/vm/RegExpObject.cpp',
        'src/vm/RegExpStatics.cpp',
        'src/vm/ScopeObject.cpp',
        'src/vm/Stack.cpp',
        'src/vm/String.cpp',
        'src/vm/StringBuffer.cpp',
        'src/vm/Unicode.cpp',
        'src/vm/Xdr.cpp',
        'src/yarr/PageBlock.cpp',
        'src/yarr/YarrInterpreter.cpp',
        'src/yarr/YarrJIT.cpp',
        'src/yarr/YarrPattern.cpp',
        'src/yarr/YarrSyntaxChecker.cpp',
      ],
    },
  ],
}
