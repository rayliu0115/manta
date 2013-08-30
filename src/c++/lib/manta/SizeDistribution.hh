// -*- mode: c++; indent-tabs-mode: nil; -*-
//
// Manta
// Copyright (c) 2013 Illumina, Inc.
//
// This software is provided under the terms and conditions of the
// Illumina Open Source Software License 1.
//
// You should have received a copy of the Illumina Open Source
// Software License 1 along with this program. If not, see
// <https://github.com/downloads/sequencing/licenses/>.
//


#pragma once

#include "boost/serialization/access.hpp"

#include <iosfwd>
#include <map>
#include <vector>


struct SizeData
{
    SizeData(
        unsigned initCount = 0,
        float initCprob = 0.) :
        count(initCount),
        cprob(initCprob)
    {}

    template<class Archive>
    void serialize(Archive& ar, const unsigned /*version*/)
    {
        ar& count;
        ar& cprob;
    }

    unsigned count;
    float cprob;
};



/// accumulate size observations and provide cdf/quantile for the distribution
///
struct SizeDistribution
{
    SizeDistribution() :
        _isStatsComputed(false),
        _totalCount(0),
        _quantiles(_quantileNum,0)
    {}

    /// return value for which we observe value or less with prob p
    int
    quantile(const float p) const;

    /// prob of observing this size or less
    float
    cdf(const int x) const;

    unsigned
    totalObservations() const
    {
        return _totalCount;
    }

    void
    addObservation(const int size)
    {
        _isStatsComputed = false;
        _totalCount++;
        _sizeMap[size].count++;
    }


    typedef std::map<int, SizeData, std::greater<int> > map_type;

private:
    void
    calcStats() const;

    friend class boost::serialization::access;
    template<class Archive>
    void serialize(Archive& ar, const unsigned /*version*/)
    {
        ar& _totalCount;
        ar& _sizeMap;
        _isStatsComputed = false;
    }


    ///////////////////////////////////// data:

    static const int _quantileNum = 1000;

    mutable bool _isStatsComputed;
    unsigned _totalCount;
    mutable std::vector<float> _quantiles;
    mutable map_type _sizeMap;
};

std::ostream&
operator<<(std::ostream& os, const SizeDistribution& sd);
