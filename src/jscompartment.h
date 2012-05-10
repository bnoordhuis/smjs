/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
 *
 * ***** BEGIN LICENSE BLOCK *****
 * Version: MPL 1.1/GPL 2.0/LGPL 2.1
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License. You may obtain a copy of the License at
 * http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 *
 * The Original Code is SpiderMonkey code.
 *
 * The Initial Developer of the Original Code is
 * Mozilla Corporation.
 * Portions created by the Initial Developer are Copyright (C) 2010
 * the Initial Developer. All Rights Reserved.
 *
 * Contributor(s):
 *
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either of the GNU General Public License Version 2 or later (the "GPL"),
 * or the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
 * in which case the provisions of the GPL or the LGPL are applicable instead
 * of those above. If you wish to allow use of your version of this file only
 * under the terms of either the GPL or the LGPL, and not to allow others to
 * use your version of this file under the terms of the MPL, indicate your
 * decision by deleting the provisions above and replace them with the notice
 * and other provisions required by the GPL or the LGPL. If you do not delete
 * the provisions above, a recipient may use your version of this file under
 * the terms of any one of the MPL, the GPL or the LGPL.
 *
 * ***** END LICENSE BLOCK ***** */

#ifndef jscompartment_h___
#define jscompartment_h___

#include "mozilla/Attributes.h"

#include "jsclist.h"
#include "jscntxt.h"
#include "jsfun.h"
#include "jsgc.h"
#include "jsobj.h"
#include "jsscope.h"
#include "vm/GlobalObject.h"
#include "vm/RegExpObject.h"

#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable:4251) /* Silence warning about JS_FRIEND_API and data members. */
#endif

namespace js {

/* Defined in jsapi.cpp */
extern Class dummy_class;

/*
 * A single-entry cache for some base-10 double-to-string conversions. This
 * helps date-format-xparb.js.  It also avoids skewing the results for
 * v8-splay.js when measured by the SunSpider harness, where the splay tree
 * initialization (which includes many repeated double-to-string conversions)
 * is erroneously included in the measurement; see bug 562553.
 */
class DtoaCache {
    double        d;
    int         base;
    JSFixedString *s;      // if s==NULL, d and base are not valid
  public:
    DtoaCache() : s(NULL) {}
    void purge() { s = NULL; }

    JSFixedString *lookup(int base, double d) {
        return this->s && base == this->base && d == this->d ? this->s : NULL;
    }

    void cache(int base, double d, JSFixedString *s) {
        this->base = base;
        this->d = d;
        this->s = s;
    }

};

/* If HashNumber grows, need to change WrapperHasher. */
JS_STATIC_ASSERT(sizeof(HashNumber) == 4);

struct WrapperHasher
{
    typedef Value Lookup;

    static HashNumber hash(Value key) {
        JS_ASSERT(!IsPoisonedValue(key));
        uint64_t bits = JSVAL_TO_IMPL(key).asBits;
        return uint32_t(bits) ^ uint32_t(bits >> 32);
    }

    static bool match(const Value &l, const Value &k) { return l == k; }
};

typedef HashMap<Value, ReadBarrieredValue, WrapperHasher, SystemAllocPolicy> WrapperMap;

} /* namespace js */

namespace JS {
struct TypeInferenceSizes;
}

struct JSCompartment
{
    JSRuntime                    *rt;
    JSPrincipals                 *principals;

    js::gc::ArenaLists           arenas;

  private:
    bool                         needsBarrier_;
  public:

    bool needsBarrier() const {
        return needsBarrier_;
    }

    void setNeedsBarrier(bool needs);

    js::GCMarker *barrierTracer() {
        JS_ASSERT(needsBarrier_);
        return &rt->gcMarker;
    }

  private:
    enum CompartmentGCState {
        NoGCScheduled,
        GCScheduled,
        GCRunning
    };

    CompartmentGCState           gcState;
    bool                         gcPreserveCode;

  public:
    bool isCollecting() const {
        /* Allow this if we're in the middle of an incremental GC. */
        if (rt->gcRunning) {
            return gcState == GCRunning;
        } else {
            JS_ASSERT(gcState != GCRunning);
            return needsBarrier();
        }
    }

    bool isPreservingCode() const {
        return gcPreserveCode;
    }

    /*
     * If this returns true, all object tracing must be done with a GC marking
     * tracer.
     */
    bool requireGCTracer() const {
        return gcState == GCRunning;
    }

    void setCollecting(bool collecting) {
        JS_ASSERT(rt->gcRunning);
        if (collecting)
            gcState = GCRunning;
        else
            gcState = NoGCScheduled;
    }

    void scheduleGC() {
        JS_ASSERT(!rt->gcRunning);
        JS_ASSERT(gcState != GCRunning);
        gcState = GCScheduled;
    }

    void unscheduleGC() {
        JS_ASSERT(!rt->gcRunning);
        JS_ASSERT(gcState != GCRunning);
        gcState = NoGCScheduled;
    }

    bool isGCScheduled() const {
        return gcState == GCScheduled;
    }

    void setPreservingCode(bool preserving) {
        gcPreserveCode = preserving;
    }

    size_t                       gcBytes;
    size_t                       gcTriggerBytes;

    bool                         hold;
    bool                         isSystemCompartment;

    int64_t                      lastCodeRelease;

    /*
     * Pool for analysis and intermediate type information in this compartment.
     * Cleared on every GC, unless the GC happens during analysis (indicated
     * by activeAnalysis, which is implied by activeInference).
     */
    static const size_t TYPE_LIFO_ALLOC_PRIMARY_CHUNK_SIZE = 128 * 1024;
    js::LifoAlloc                typeLifoAlloc;
    bool                         activeAnalysis;
    bool                         activeInference;

    /* Type information about the scripts and objects in this compartment. */
    js::types::TypeCompartment   types;

    void                         *data;
    bool                         active;  // GC flag, whether there are active frames
    js::WrapperMap               crossCompartmentWrappers;

    /* Last time at which an animation was played for a global in this compartment. */
    int64_t                      lastAnimationTime;

    js::RegExpCompartment        regExps;

    size_t sizeOfShapeTable(JSMallocSizeOfFun mallocSizeOf);
    void sizeOfTypeInferenceData(JS::TypeInferenceSizes *stats, JSMallocSizeOfFun mallocSizeOf);

    /*
     * Shared scope property tree, and arena-pool for allocating its nodes.
     */
    js::PropertyTree             propertyTree;

    /* Set of all unowned base shapes in the compartment. */
    js::BaseShapeSet             baseShapes;
    void sweepBaseShapeTable();

    /* Set of initial shapes in the compartment. */
    js::InitialShapeSet          initialShapes;
    void sweepInitialShapeTable();

    /* Set of default 'new' or lazy types in the compartment. */
    js::types::TypeObjectSet     newTypeObjects;
    js::types::TypeObjectSet     lazyTypeObjects;
    void sweepNewTypeObjectTable(js::types::TypeObjectSet &table);

    js::types::TypeObject        *emptyTypeObject;

    /* Get the default 'new' type for objects with a NULL prototype. */
    inline js::types::TypeObject *getEmptyType(JSContext *cx);

    js::types::TypeObject *getLazyType(JSContext *cx, JSObject *proto);

    /*
     * Keeps track of the total number of malloc bytes connected to a
     * compartment's GC things. This counter should be used in preference to
     * gcMallocBytes. These counters affect collection in the same way as
     * gcBytes and gcTriggerBytes.
     */
    size_t                       gcMallocAndFreeBytes;
    size_t                       gcTriggerMallocAndFreeBytes;

  private:
    /*
     * Malloc counter to measure memory pressure for GC scheduling. It runs from
     * gcMaxMallocBytes down to zero. This counter should be used only when it's
     * not possible to know the size of a free.
     */
    size_t                       gcMallocBytes;
    size_t                       gcMaxMallocBytes;

    enum { DebugFromC = 1, DebugFromJS = 2 };

    unsigned                     debugModeBits;  // see debugMode() below

  public:
    JSCompartment(JSRuntime *rt);
    ~JSCompartment();

    bool init(JSContext *cx);

    /* Mark cross-compartment wrappers. */
    void markCrossCompartmentWrappers(JSTracer *trc);

    bool wrap(JSContext *cx, js::Value *vp);
    bool wrap(JSContext *cx, JSString **strp);
    bool wrap(JSContext *cx, js::HeapPtrString *strp);
    bool wrap(JSContext *cx, JSObject **objp);
    bool wrapId(JSContext *cx, jsid *idp);
    bool wrap(JSContext *cx, js::PropertyOp *op);
    bool wrap(JSContext *cx, js::StrictPropertyOp *op);
    bool wrap(JSContext *cx, js::PropertyDescriptor *desc);
    bool wrap(JSContext *cx, js::AutoIdVector &props);

    void markTypes(JSTracer *trc);
    void discardJitCode(js::FreeOp *fop);
    void sweep(js::FreeOp *fop, bool releaseTypes);
    void purge();

    void setGCLastBytes(size_t lastBytes, size_t lastMallocBytes, js::JSGCInvocationKind gckind);
    void reduceGCTriggerBytes(size_t amount);

    void resetGCMallocBytes();
    void setGCMaxMallocBytes(size_t value);
    void updateMallocCounter(size_t nbytes) {
        size_t oldCount = gcMallocBytes;
        size_t newCount = oldCount - nbytes;
        gcMallocBytes = newCount;
        // gcMallocBytes will wrap around and be bigger than gcMaxAllocBytes if a signed value
        // would be < 0
        if (JS_UNLIKELY(oldCount <= gcMaxMallocBytes && newCount > gcMaxMallocBytes))
            onTooMuchMalloc();
    }

    bool isTooMuchMalloc() const {
        return gcMallocBytes > gcMaxMallocBytes;
     }

    void onTooMuchMalloc();

    void mallocInCompartment(size_t nbytes) {
        gcMallocAndFreeBytes += nbytes;
    }

    void freeInCompartment(size_t nbytes) {
        JS_ASSERT(gcMallocAndFreeBytes >= nbytes);
        gcMallocAndFreeBytes -= nbytes;
    }

    js::DtoaCache dtoaCache;

  private:
    /*
     * Weak reference to each global in this compartment that is a debuggee.
     * Each global has its own list of debuggers.
     */
    js::GlobalObjectSet              debuggees;

  private:
    JSCompartment *thisForCtor() { return this; }

  public:
    /*
     * There are dueling APIs for debug mode. It can be enabled or disabled via
     * JS_SetDebugModeForCompartment. It is automatically enabled and disabled
     * by Debugger objects. Therefore debugModeBits has the DebugFromC bit set
     * if the C API wants debug mode and the DebugFromJS bit set if debuggees
     * is non-empty.
     */
    bool debugMode() const { return !!debugModeBits; }

    /* True if any scripts from this compartment are on the JS stack. */
    bool hasScriptsOnStack();

  private:
    /* This is called only when debugMode() has just toggled. */
    void updateForDebugMode(js::FreeOp *fop);

  public:
    js::GlobalObjectSet &getDebuggees() { return debuggees; }
    bool addDebuggee(JSContext *cx, js::GlobalObject *global);
    void removeDebuggee(js::FreeOp *fop, js::GlobalObject *global,
                        js::GlobalObjectSet::Enum *debuggeesEnum = NULL);
    bool setDebugModeFromC(JSContext *cx, bool b);

    void clearBreakpointsIn(js::FreeOp *fop, js::Debugger *dbg, JSObject *handler);
    void clearTraps(js::FreeOp *fop);

  private:
    void sweepBreakpoints(js::FreeOp *fop);

  public:
    js::WatchpointMap *watchpointMap;

    js::ScriptCountsMap *scriptCountsMap;

    js::SourceMapMap *sourceMapMap;

    js::DebugScriptMap *debugScriptMap;
};

#define JS_PROPERTY_TREE(cx)    ((cx)->compartment->propertyTree)

inline void
JSContext::setCompartment(JSCompartment *compartment)
{
    this->compartment = compartment;
    this->inferenceEnabled = compartment ? compartment->types.inferenceEnabled : false;
}

#ifdef _MSC_VER
#pragma warning(pop)
#endif

namespace js {

class PreserveCompartment {
  protected:
    JSContext *cx;
  private:
    JSCompartment *oldCompartment;
    bool oldInferenceEnabled;
    JS_DECL_USE_GUARD_OBJECT_NOTIFIER
  public:
     PreserveCompartment(JSContext *cx JS_GUARD_OBJECT_NOTIFIER_PARAM) : cx(cx) {
        JS_GUARD_OBJECT_NOTIFIER_INIT;
        oldCompartment = cx->compartment;
        oldInferenceEnabled = cx->inferenceEnabled;
    }

    ~PreserveCompartment() {
        /* The old compartment may have been destroyed, so we can't use cx->setCompartment. */
        cx->compartment = oldCompartment;
        cx->inferenceEnabled = oldInferenceEnabled;
    }
};

class SwitchToCompartment : public PreserveCompartment {
  public:
    SwitchToCompartment(JSContext *cx, JSCompartment *newCompartment
                        JS_GUARD_OBJECT_NOTIFIER_PARAM)
        : PreserveCompartment(cx)
    {
        JS_GUARD_OBJECT_NOTIFIER_INIT;
        cx->setCompartment(newCompartment);
    }

    SwitchToCompartment(JSContext *cx, JSObject *target JS_GUARD_OBJECT_NOTIFIER_PARAM)
        : PreserveCompartment(cx)
    {
        JS_GUARD_OBJECT_NOTIFIER_INIT;
        cx->setCompartment(target->compartment());
    }

    JS_DECL_USE_GUARD_OBJECT_NOTIFIER
};

class AssertCompartmentUnchanged {
  protected:
    JSContext * const cx;
    JSCompartment * const oldCompartment;
    JS_DECL_USE_GUARD_OBJECT_NOTIFIER
  public:
     AssertCompartmentUnchanged(JSContext *cx JS_GUARD_OBJECT_NOTIFIER_PARAM)
     : cx(cx), oldCompartment(cx->compartment) {
        JS_GUARD_OBJECT_NOTIFIER_INIT;
    }

    ~AssertCompartmentUnchanged() {
        JS_ASSERT(cx->compartment == oldCompartment);
    }
};

class AutoCompartment
{
  public:
    JSContext * const context;
    JSCompartment * const origin;
    JSObject * const target;
    JSCompartment * const destination;
  private:
    Maybe<DummyFrameGuard> frame;
    bool entered;

  public:
    AutoCompartment(JSContext *cx, JSObject *target);
    ~AutoCompartment();

    bool enter();
    void leave();

  private:
    AutoCompartment(const AutoCompartment &) MOZ_DELETE;
    AutoCompartment & operator=(const AutoCompartment &) MOZ_DELETE;
};

/*
 * Use this to change the behavior of an AutoCompartment slightly on error. If
 * the exception happens to be an Error object, copy it to the origin compartment
 * instead of wrapping it.
 */
class ErrorCopier
{
    AutoCompartment &ac;
    RootedVarObject scope;

  public:
    ErrorCopier(AutoCompartment &ac, JSObject *scope) : ac(ac), scope(ac.context, scope) {
        JS_ASSERT(scope->compartment() == ac.origin);
    }
    ~ErrorCopier();
};

class CompartmentsIter {
  private:
    JSCompartment **it, **end;

  public:
    CompartmentsIter(JSRuntime *rt) {
        it = rt->compartments.begin();
        end = rt->compartments.end();
    }

    bool done() const { return it == end; }

    void next() {
        JS_ASSERT(!done());
        it++;
    }

    JSCompartment *get() const {
        JS_ASSERT(!done());
        return *it;
    }

    operator JSCompartment *() const { return get(); }
    JSCompartment *operator->() const { return get(); }
};

} /* namespace js */

#endif /* jscompartment_h___ */
