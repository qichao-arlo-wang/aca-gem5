/*
 * Copyright (c) 2012, 2014, 2020 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2004-2006 The Regents of The University of Michigan
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __CPU_O3_MEM_DEP_UNIT_HH__
#define __CPU_O3_MEM_DEP_UNIT_HH__

#include <list>
#include <memory>
#include <set>
#include <unordered_map>
#include <unordered_set>

// #include "base/statistics.hh"
// #include "cpu/inst_seq.hh"
// #include "cpu/o3/dyn_inst_ptr.hh"
// #include "cpu/o3/limits.hh"
// #include "cpu/o3/phast.hh"
// #include "debug/MemDepUnit.hh"
#include "base/statistics.hh"
#include "cpu/inst_seq.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "cpu/o3/limits.hh"
#include "cpu/o3/phast.hh"
//#include "cpu/o3/store_set.hh"
#include "debug/MemDepUnit.hh"
#include "mem/packet.hh"
#include "mem/port.hh"

namespace gem5
{

struct SNHash
{
    size_t
    operator()(const InstSeqNum &seq_num) const
    {
        unsigned a = (unsigned)seq_num;
        unsigned hash = (((a >> 14) ^ ((a >> 2) & 0xffff))) & 0x7FFFFFFF;
        return hash;
    }
};

struct BaseO3CPUParams;

namespace o3
{

// class PHAST;
//class StoreSet;
class CPU;
class InstructionQueue;

struct PredictionResult {
    /* For StoreSets */
    InstSeqNum seqNum;
    /* For PHAST */
    std::ptrdiff_t storeQueueDistance;
    unsigned predBranchHistLength;
    uint64_t predictorHash;
};

/**
 * Memory dependency unit class.  This holds the memory dependence predictor.
 * As memory operations are issued to the IQ, they are also issued to this
 * unit, which then looks up the prediction as to what they are dependent
 * upon.  This unit must be checked prior to a memory operation being able
 * to issue.  Although this is templated, it's somewhat hard to make a generic
 * memory dependence unit.  This one is mostly for store sets; it will be
 * quite limited in what other memory dependence predictions it can also
 * utilize.  Thus this class should be most likely be rewritten for other
 * dependence prediction schemes.
 */
class MemDepUnit
{
  protected:
    std::string _name;

  public:
    /** Empty constructor. Must call init() prior to using in this case. */
    MemDepUnit();

    /** Constructs a MemDepUnit with given parameters. */
    MemDepUnit(const BaseO3CPUParams &params);

    /** Frees up any memory allocated. */
    ~MemDepUnit();

    /** Returns the name of the memory dependence unit. */
    std::string name() const { return _name; }

    /** Initializes the unit with parameters and a thread id. */
    void init(const BaseO3CPUParams &params, ThreadID tid, CPU *_cpu);

    /** Determine if we are drained. */
    bool isDrained() const;

    /** Perform sanity checks after a drain. */
    void drainSanityCheck() const;

    /** Takes over from another CPU's thread. */
    void takeOverFrom();

    void clear_dep_pred();

    /** Sets the pointer to the IQ. */
    void setIQ(InstructionQueue *iq_ptr);

    /** Inserts a memory instruction. */
    void insert(const DynInstPtr &inst, BranchHistory branchHistory);

    /** Inserts a non-speculative memory instruction. */
    void insertNonSpec(const DynInstPtr &inst);

    /** Inserts a barrier instruction. */
    void insertBarrier(const DynInstPtr &barr_inst);

    /** Indicate that an instruction has its registers ready. */
    void regsReady(const DynInstPtr &inst);

    /** Indicate that a non-speculative instruction is ready. */
    void nonSpecInstReady(const DynInstPtr &inst);

    /** Reschedules an instruction to be re-executed. */
    void reschedule(const DynInstPtr &inst);

    /** Replays all instructions that have been rescheduled by moving them to
     *  the ready list.
     */
    void replay();

    /** Notifies completion of an instruction. */
    void completeInst(const DynInstPtr &inst);

    /** Squashes all instructions up until a given sequence number for a
     *  specific thread.
     */
    void squash(const InstSeqNum &squashed_num, ThreadID tid);

    /** Indicates an ordering violation between a store and a younger load. */
    void violation(InstSeqNum store_seq_num, Addr store_pc, const DynInstPtr &violating_load,
                   BranchHistory branchHistory);

    /** Issues the given instruction */
    void issue(const DynInstPtr &inst);

    /** Commits the given instruction */
    void commit(const DynInstPtr &inst);

    /** Debugging function to dump the lists of instructions. */
    void dumpLists();

    /** The thread id of this memory dependence unit. */
    int id;
    struct MemDepUnitStats : public statistics::Group
    {
        MemDepUnitStats(statistics::Group *parent);
        /** Stat for number of inserted loads. */
        statistics::Scalar insertedLoads;
        /** Stat for number of inserted stores. */
        statistics::Scalar insertedStores;
        /** Stat for number of conflicting loads that had to wait for a
         *  store. */
        statistics::Scalar conflictingLoads;
        /** Stat for number of conflicting stores that had to wait for a
         *  store. */
        statistics::Scalar conflictingStores;
        /* Number of false dependencies predicted by depPred */
        statistics::Scalar falseDependencies;
        /* Number of true dependencies predicted by depPred */
        statistics::Scalar correctPredictions;
        /** ==== Store Sets ==== */
        statistics::Scalar LFSTReads;
        statistics::Scalar LFSTWrites;
        /**  Sorry for this. Need to track reads/writes for each
         *  specific branch len table for power usage estimation. */
        statistics::Scalar readsPath1;
        statistics::Scalar readsPath2;
        statistics::Scalar readsPath3;
        statistics::Scalar readsPath4;
        statistics::Scalar readsPath5;
        statistics::Scalar readsPath6;
        statistics::Scalar readsPath7;
        statistics::Scalar readsPath8;
        statistics::Scalar writesPath1;
        statistics::Scalar writesPath2;
        statistics::Scalar writesPath3;
        statistics::Scalar writesPath4;
        statistics::Scalar writesPath5;
        statistics::Scalar writesPath6;
        statistics::Scalar writesPath7;
        statistics::Scalar writesPath8;
    } stats;

    statistics::Scalar *pathReads[8] = {
        &(stats.readsPath1), &(stats.readsPath2),
        &(stats.readsPath3), &(stats.readsPath4),
        &(stats.readsPath5), &(stats.readsPath6),
        &(stats.readsPath7), &(stats.readsPath8)
    };
    statistics::Scalar *pathWrites[8] = {
        &(stats.writesPath1), &(stats.writesPath2),
        &(stats.writesPath3), &(stats.writesPath4),
        &(stats.writesPath5), &(stats.writesPath6),
        &(stats.writesPath7), &(stats.writesPath8)
    };

    CPU *cpu;

  private:

    /** Completes a memory instruction. */
    void completed(const DynInstPtr &inst);

    /** Wakes any dependents of a memory instruction. */
    void wakeDependents(const DynInstPtr &inst);

    typedef typename std::list<DynInstPtr>::iterator ListIt;

    class MemDepEntry;

    typedef std::shared_ptr<MemDepEntry> MemDepEntryPtr;

    /** Memory dependence entries that track memory operations, marking
     *  when the instruction is ready to execute and what instructions depend
     *  upon it.
     */
    class MemDepEntry
    {
      public:
        /** Constructs a memory dependence entry. */
        MemDepEntry(const DynInstPtr &new_inst);

        /** Frees any pointers. */
        ~MemDepEntry();

        /** Returns the name of the memory dependence entry. */
        std::string name() const { return "memdepentry"; }

        /** The instruction being tracked. */
        DynInstPtr inst;

        /** The iterator to the instruction's location inside the list. */
        ListIt listIt;

        /** A vector of any dependent instructions. */
        std::vector<MemDepEntryPtr> dependInsts;

        /** If the registers are ready or not. */
        bool regsReady = false;
        /** Number of memory dependencies that need to be satisfied. */
        int memDeps = 0;
        /** If the instruction is completed. */
        bool completed = false;
        /** If the instruction is squashed. */
        bool squashed = false;

        /** For debugging. */
#ifdef GEM5_DEBUG
        static int memdep_count;
        static int memdep_insert;
        static int memdep_erase;
#endif
    };

    /** Finds the memory dependence entry in the hash map. */
    MemDepEntryPtr &findInHash(const DynInstConstPtr& inst);

    /** Moves an entry to the ready list. */
    void moveToReady(MemDepEntryPtr &ready_inst_entry);

    typedef std::unordered_map<InstSeqNum, MemDepEntryPtr, SNHash> MemDepHash;

    typedef typename MemDepHash::iterator MemDepHashIt;

    /** A hash map of all memory dependence entries. */
    MemDepHash memDepHash;

    /** A list of all instructions in the memory dependence unit. */
    std::list<DynInstPtr> instList[MaxThreads];

    /** A list of all instructions that are going to be replayed. */
    std::list<DynInstPtr> instsToReplay;

    /** The memory dependence predictor.  It is accessed upon new
     *  instructions being added to the IQ, and responds by telling
     *  this unit what instruction the newly added instruction is dependent
     *  upon.
     */
    PHAST depPred;

    /** Sequence numbers of outstanding load barriers. */
    std::unordered_set<InstSeqNum> loadBarrierSNs;

    /** Sequence numbers of outstanding store barriers. */
    std::unordered_set<InstSeqNum> storeBarrierSNs;

    /** Is there an outstanding load barrier that loads must wait on. */
    bool hasLoadBarrier() const { return !loadBarrierSNs.empty(); }

    /** Is there an outstanding store barrier that loads must wait on. */
    bool hasStoreBarrier() const { return !storeBarrierSNs.empty(); }

    /** Inserts the SN of a barrier inst. to the list of tracked barriers */
    void insertBarrierSN(const DynInstPtr &barr_inst);

    /** Pointer to the IQ. */
    InstructionQueue *iqPtr;

};

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_MEM_DEP_UNIT_HH__
