/*
 * Souffle - A Datalog Compiler
 * Copyright (c) 2022, The Souffle Developers. All rights reserved
 * Licensed under the Universal Permissive License v 1.0 as shown at:
 * - https://opensource.org/licenses/UPL
 * - <souffle root>/licenses/SOUFFLE-UPL.txt
 */

#include "souffle/SouffleFunctor.h"

extern "C" {

souffle::RamDomain f(souffle::SymbolTable*, souffle::RecordTable*) {
    return 1;
}

}  // end of extern "C"
